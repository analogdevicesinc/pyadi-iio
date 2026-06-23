#!/usr/bin/env python3
"""Boot the board referenced by LG_ENV and print its live ``ip:<addr>`` URI.

Used in the hw-matrix dynamic_mode leg as a prologue to pytest: after
labgrid acquires the place, transition the Strategy to ``shell`` and poll
the DUT's eth0 for its DHCP-assigned IPv4 address. That address is the
source of truth — the exporter-side ``NetworkService.address`` record goes
stale every reboot.

Mirrors ``test/hw/conftest.py::_discover_iio_uri_via_labgrid`` so the CI
prologue and the in-test fallback resolve identically.

Exits non-zero with a message on stderr on failure.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time

POLL_ATTEMPTS = 45
POLL_INTERVAL_S = 2
# A boot can fail transiently (stale serial session from a prior run, a
# 30s pexpect timeout, a missed DHCP lease). labgrid pins a Strategy
# ``broken`` after any transition exception, so a retry MUST reconstruct
# the Environment to get a fresh Strategy — a fresh Strategy starts at
# ``status=unknown`` and walks the full power-cycle chain again.
BOOT_RETRIES = 1
BOOT_RETRY_DELAY_S = 5


def _trust_exporter_host(host: str) -> None:
    """Pre-seed ~/.ssh/known_hosts for the exporter SSH proxy hop.

    labgrid's NetworkSerialPort is proxied through SSH to the exporter
    host (named after the place by lab convention). Without the host key
    pre-trusted, ssh fails with "Host key verification failed". The
    runner is inside the lab network and the exporter is a known
    long-lived host, so trust-on-first-use is acceptable here.
    """
    if not host:
        return
    ssh_dir = pathlib.Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    known_hosts = ssh_dir / "known_hosts"
    try:
        result = subprocess.run(
            ["ssh-keyscan", "-T", "5", "-H", host],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"ssh-keyscan {host} failed: {exc}", file=sys.stderr)
        return
    if result.returncode != 0 or not result.stdout:
        # Don't hard-fail — let the downstream SSH attempt produce its own error
        # if it can't connect, but keep the message in the log for diagnostics.
        print(
            f"ssh-keyscan {host} returned no keys (rc={result.returncode}); continuing",
            file=sys.stderr,
        )
        return
    with known_hosts.open("a", encoding="utf-8") as fh:
        fh.write(result.stdout)
    print(f"[boot-and-discover] trusted host key(s) for '{host}'", file=sys.stderr)


def _boot_and_discover(lg_env: str) -> str:
    """Build a fresh Environment, boot to ``shell``, return the eth0 IPv4.

    Constructs the labgrid Environment from scratch on every call so a
    Strategy left ``broken`` by a prior attempt never poisons this one.
    Raises on any boot/transition failure or if DHCP never assigns an
    address; the caller decides whether to retry.
    """
    from labgrid.environment import Environment
    from labgrid.strategy import Strategy

    env = Environment(lg_env)
    target = env.get_target("main")
    strategy = target.get_driver(Strategy)
    print(f"Strategy: {strategy}", file=sys.stderr)
    strategy.transition("shell")

    try:
        shell = target.get_driver("ADIShellDriver")
    except Exception:
        shell = target.get_driver("ShellDriver")

    for _ in range(POLL_ATTEMPTS):
        out, _err, rc = shell.run(
            "ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1"
        )
        if rc == 0 and out and out[0].strip():
            return out[0].strip()
        time.sleep(POLL_INTERVAL_S)

    raise RuntimeError(
        f"eth0 has no IPv4 address {POLL_ATTEMPTS * POLL_INTERVAL_S}s after shell "
        "prompt; DHCP failed?"
    )


def main() -> int:
    lg_env = os.environ.get("LG_ENV")
    if not lg_env:
        print("LG_ENV not set", file=sys.stderr)
        return 2

    # labgrid proxies to the exporter host by name; the place name matches the
    # exporter name in this lab. Pre-trust the host key so SSHDriver doesn't
    # die on "Host key verification failed".
    _trust_exporter_host(os.environ.get("LG_PLACE", ""))

    try:
        import labgrid.environment  # noqa: F401
    except ImportError as exc:
        print(f"labgrid not importable: {exc}", file=sys.stderr)
        return 1

    last_err: Exception | None = None
    for attempt in range(1, BOOT_RETRIES + 2):
        try:
            address = _boot_and_discover(lg_env)
            print(f"ip:{address}")
            return 0
        except Exception as exc:
            last_err = exc
            if attempt > BOOT_RETRIES:
                break
            print(
                f"[boot-and-discover] attempt {attempt} failed ({exc}); "
                "reconstructing labgrid Environment for cold-cycle retry",
                file=sys.stderr,
            )
            time.sleep(BOOT_RETRY_DELAY_S)

    print(
        f"boot/discover failed after {BOOT_RETRIES + 1} attempts: {last_err}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
