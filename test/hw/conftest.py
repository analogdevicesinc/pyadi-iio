"""HW-test conftest.

Resolves a libiio URI for tests under ``test/hw/`` by either:
  1. ``--iio-uri-override <uri>`` / ``IIO_URI_OVERRIDE`` env var (laptop runs).
  2. ``--uri <uri>`` from pytest-libiio (used by the hw-matrix CI prologue,
     which boots the board out-of-band and exports the URI).
  3. The labgrid env at ``LG_ENV`` — load the environment, transition the
     board's Strategy to ``shell`` (booting it if needed), then query the
     DUT's actual eth0 IP via the ADIShellDriver. The exporter's static
     ``NetworkService.address`` is not reliable because DUTs DHCP a fresh
     IP every boot; the post-boot shell is the source of truth.

Whichever path produces the URI, we then poll the iiod userspace until a
libiio context opens cleanly — DHCP'ing eth0 does NOT mean iiod is ready
(IIO drivers can take another 5-15s to probe, especially on cold boots).

If discovery+wait fails, we retry the whole sequence once with a fresh
labgrid Environment so the Strategy state machine resets (labgrid's
``@never_retry`` decorator pins a broken Strategy permanently otherwise).
This catches one-shot serial drops, power-controller blips, and similar
transient bootstrap flakes that would otherwise redden CI.

This file only applies to tests collected under ``test/hw/``. The historic
``test/conftest.py`` (libiio-plugin-driven suite) is untouched.
"""

from __future__ import annotations

import os
import sys
import time

import pytest


def pytest_addoption(parser):
    g = parser.getgroup("hw")
    g.addoption(
        "--iio-uri-override",
        default=os.environ.get("IIO_URI_OVERRIDE"),
        help="Bypass labgrid; libiio URI to point tests at (e.g. ip:10.0.0.132).",
    )


def _discover_iio_uri_via_labgrid(lg_env_path: str) -> str:
    """Boot the board (if needed) and return ``ip:<eth0-address>``.

    Loads the labgrid Environment, transitions Strategy to ``shell``, then
    runs ``ip addr`` over the ADIShellDriver to read the DUT's DHCP IP.

    A fresh ``Environment`` is constructed every call so the retry path in
    ``_discover_with_retry`` gets a clean Strategy instance (labgrid marks
    a Strategy ``broken`` after any transition exception and refuses
    further transitions until reset).
    """
    from labgrid.environment import Environment
    from labgrid.strategy import Strategy

    env = Environment(lg_env_path)
    target = env.get_target("main")

    strategy = target.get_driver(Strategy)
    strategy.transition("shell")

    # ADIShellDriver from adi_lg_plugins; fall back to the stock ShellDriver
    # name lookup if a yaml ever declares it that way.
    try:
        shell = target.get_driver("ADIShellDriver")
    except Exception:
        shell = target.get_driver("ShellDriver")

    # Reaching the shell prompt is async with DHCP. Poll until eth0 has a
    # routable IPv4 address (or until ~90s elapses — the lab DHCP server
    # is on the same subnet so leases land in a few seconds in practice).
    address = ""
    for _ in range(45):
        out, _err, rc = shell.run(
            "ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1"
        )
        if rc == 0 and out and out[0].strip():
            address = out[0].strip()
            break
        time.sleep(2)
    if not address:
        raise RuntimeError(
            "eth0 has no IPv4 address 90s after shell prompt; DHCP failed?"
        )
    print(f"[iio_uri] discovered DUT IP {address} from {lg_env_path}", file=sys.stderr)
    return f"ip:{address}"


def _wait_for_iiod_ready(uri: str, timeout: float = 60.0) -> None:
    """Block until ``iio.Context(uri)`` succeeds or ``timeout`` elapses.

    eth0 being up does not mean iiod can accept TCP/IP connections — the
    userspace daemon races kernel-module probing of the IIO devices for
    seconds after the shell login prompt. Without this wait the first
    test reliably races and dies with ``Unable to open context``.
    """
    import iio

    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            ctx = iio.Context(uri)
            # Reading attrs forces a real round-trip; ``Context()`` alone
            # has been observed to return on half-initialized daemons.
            _ = ctx.attrs
            return
        except Exception as exc:
            last_err = exc
            time.sleep(1)
    raise RuntimeError(
        f"iiod at {uri} not ready after {timeout:.0f}s; last error: {last_err}"
    )


def _discover_and_validate(lg_env_path: str) -> str:
    """One full pass: boot via labgrid, then wait for iiod to be reachable."""
    uri = _discover_iio_uri_via_labgrid(lg_env_path)
    _wait_for_iiod_ready(uri, timeout=60.0)
    return uri


def _discover_with_retry(lg_env_path: str, retries: int = 1) -> str:
    """Discover + iiod-wait with bounded retries on any transient failure.

    Each retry reconstructs the labgrid Environment so the Strategy's
    ``broken`` state (set by labgrid's @never_retry wrapper on first
    failure) doesn't poison the second attempt. A fresh Strategy starts
    at ``status=unknown``, so its first transition walks the full
    ``powered_off → ... → shell`` chain — effectively a cold cycle.
    """
    last_err: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            return _discover_and_validate(lg_env_path)
        except Exception as exc:
            last_err = exc
            if attempt > retries:
                raise
            print(
                f"[iio_uri] attempt {attempt} failed ({exc}); "
                "reloading labgrid Environment for cold-cycle retry",
                file=sys.stderr,
            )
            time.sleep(5)
    # Unreachable; the loop either returns or re-raises.
    raise RuntimeError(f"discovery exhausted retries: {last_err}")


def _get_pytest_libiio_uri(request) -> str | None:
    """Return ``--uri`` from pytest-libiio if registered, else None.

    pytest-libiio adds ``--uri`` for the legacy suite; the hw-matrix CI
    prologue passes ``--uri=$DUT_URI`` after its own boot-and-discover
    step. When that arg is present we honor it instead of re-bootstrapping
    via labgrid — the board is already up.
    """
    try:
        return request.config.getoption("--uri")
    except (ValueError, KeyError):
        return None


@pytest.fixture(scope="session")
def iio_uri(request) -> str:
    """Return an ``ip:...`` URI to a real iiod.

    Resolution order:
      1. ``--iio-uri-override`` / ``IIO_URI_OVERRIDE`` (manual override).
      2. ``--uri`` from pytest-libiio (CI prologue path).
      3. ``LG_ENV`` — load the labgrid env yaml, boot the board, discover
         its IP via the serial-console shell.

    Every returned URI is validated by waiting for iiod to accept a
    libiio context. The labgrid path also retries once on any transient
    bootstrap failure (with a fresh Environment, effectively cold-cycling
    the board).
    """
    override = request.config.getoption("--iio-uri-override")
    if override:
        _wait_for_iiod_ready(override, timeout=30.0)
        return override

    pl_uri = _get_pytest_libiio_uri(request)
    if pl_uri:
        _wait_for_iiod_ready(pl_uri, timeout=30.0)
        return pl_uri

    lg_env = os.environ.get("LG_ENV")
    if not lg_env:
        # Emulated-HW CI collects everything under test/ but doesn't (and
        # can't) boot real hardware: `--emu-xml-dir` is wired in by the
        # pyproject.toml addopts. Skip these labgrid-only smoke tests
        # cleanly in that context; save the loud failure for the real HW
        # pipelines below where the pyproject addopts is also active but
        # LG_ENV / --uri / --iio-uri-override is also provided.
        try:
            emu_xml_dir = request.config.getoption("--emu-xml-dir")
        except (ValueError, KeyError):
            emu_xml_dir = None
        if emu_xml_dir:
            pytest.skip(
                f"emu mode (--emu-xml-dir={emu_xml_dir}); test/hw/ smoke "
                "tests require real hardware via LG_ENV/--uri/--iio-uri-override."
            )
        pytest.fail(
            "no IIO URI source: pass --iio-uri-override, --uri, or set LG_ENV "
            "(the hw-matrix CI workflow exports this automatically)."
        )

    try:
        import adi_lg_plugins  # noqa: F401
        import labgrid  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"labgrid stack not importable ({exc}); install adi-labgrid-plugins "
            "or pass --iio-uri-override."
        )

    try:
        return _discover_with_retry(lg_env, retries=1)
    except Exception as exc:
        pytest.fail(f"iio_uri discovery failed: {exc}")
