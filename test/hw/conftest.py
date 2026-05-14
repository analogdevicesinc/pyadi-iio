"""HW-test conftest.

Bridges the labgrid place held by the calling workflow (or a manually-set
LG_PLACE / LG_COORDINATOR pair) into a libiio URI usable by ``adi``
device classes.

Used by the new GH Actions hardware-test workflow (which calls
labgrid-plugins' hw-matrix reusable workflow). Tests under ``test/hw/``
take an ``iio_uri`` fixture and instantiate the device class with it.

When LG_ENV / LG_PLACE / LG_COORDINATOR are unset, the suite falls back
to a single ``--iio-uri-override`` CLI option (or the IIO_URI_OVERRIDE
env var) so local manual runs without labgrid still work.

Sibling test/conftest.py (the historic libiio-plugin-driven suite under
test/) is untouched; this conftest only applies to tests collected
under test/hw/.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


def pytest_addoption(parser):
    g = parser.getgroup("hw")
    g.addoption(
        "--iio-uri-override",
        default=os.environ.get("IIO_URI_OVERRIDE"),
        help="Bypass labgrid; libiio URI to point tests at (e.g. ip:10.0.0.132).",
    )


def _labgrid_show(coord: str, place: str):
    """Run `python -m labgrid.remote.client -p PLACE show` and return stdout."""
    return subprocess.run(
        [sys.executable, "-m", "labgrid.remote.client", "-x", coord, "-p", place, "show"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


@pytest.fixture(scope="session")
def iio_uri(request) -> str:
    """Return an `ip:...` URI to a real-iiod we can talk to.

    Resolution order:
      1. ``--iio-uri-override <uri>`` or ``IIO_URI_OVERRIDE`` env var
      2. The labgrid place named by ``LG_PLACE`` on ``LG_COORDINATOR``
         (set by the reusable HW workflow before pytest runs; the
         place is already acquired at workflow level).
    """
    override = request.config.getoption("--iio-uri-override")
    if override:
        return override

    coord = os.environ.get("LG_COORDINATOR")
    place = os.environ.get("LG_PLACE")
    if not (coord and place):
        pytest.skip(
            "no IIO URI source: set --iio-uri-override, or run under the "
            "HW workflow which exports LG_COORDINATOR + LG_PLACE"
        )

    try:
        import labgrid  # noqa: F401
    except ImportError:
        pytest.skip("labgrid not importable; pass --iio-uri-override instead")

    show = _labgrid_show(coord, place)
    if show.returncode != 0 or "Place" not in show.stdout:
        pytest.skip(
            f"labgrid place {place!r} unavailable at {coord}: "
            f"{show.stdout.strip()} {show.stderr.strip()}"
        )

    address = None
    for line in show.stdout.splitlines():
        s = line.strip()
        if s.startswith(("address:", "host:", "ipaddr:")):
            address = s.split(":", 1)[1].strip()
            break
    if not address:
        pytest.skip(
            f"labgrid place {place!r} has no NetworkService address — "
            "verify the exporter publishes one"
        )
    return f"ip:{address}"
