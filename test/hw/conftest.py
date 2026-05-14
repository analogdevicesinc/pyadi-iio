"""HW-test conftest.

Resolves a libiio URI for tests under ``test/hw/``. The URI is **always**
supplied explicitly via ``--iio-uri-override``; there is no implicit
labgrid/coordinator lookup. The caller (CI workflow or local user) is
responsible for naming the exact board to talk to — this avoids any
chance of pytest connecting to a stray board that happens to be on the
network.

Used by the GH Actions hardware-test workflow, which acquires the
place, boots it, reads eth0's IP from the live serial console, and
passes ``--iio-uri-override ip:<real-ip>`` to pytest.

Sibling ``test/conftest.py`` (the historic libiio-plugin-driven suite
under ``test/``) is untouched; this conftest only applies to tests
collected under ``test/hw/``.
"""

from __future__ import annotations

import os

import pytest


def pytest_addoption(parser):
    g = parser.getgroup("hw")
    g.addoption(
        "--iio-uri-override",
        default=os.environ.get("IIO_URI_OVERRIDE", ""),
        help=(
            "libiio URI for the DUT (e.g. ip:10.0.0.211). Required for tests "
            "under test/hw/. Defaults to the IIO_URI_OVERRIDE env var when "
            "unset on the CLI."
        ),
    )


@pytest.fixture(scope="session")
def iio_uri(request) -> str:
    """Return the explicitly-named DUT URI.

    Tests are skipped if no URI was passed — the conftest deliberately
    refuses to auto-discover, so an unrelated board on the LAN can't be
    poked by accident.
    """
    uri = (request.config.getoption("--iio-uri-override") or "").strip()
    if not uri:
        pytest.skip(
            "no DUT URI provided. Pass --iio-uri-override ip:<host> on the "
            "pytest CLI (the reusable hw-matrix-v2 workflow does this "
            "automatically after reading eth0 from the booted board's "
            "serial console)."
        )
    return uri
