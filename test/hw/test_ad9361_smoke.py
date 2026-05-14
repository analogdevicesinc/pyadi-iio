"""Smoke test: open a libiio context against an AD9361-based board (FMComms2/3).

Run under the new GH Actions HW workflow with LG_COORDINATOR + LG_PLACE
set (see conftest.py), or locally via:

    pytest -v test/hw/test_ad9361_smoke.py --iio-uri-override ip:10.0.0.50
"""

from __future__ import annotations

import pytest

import adi


def test_open_context(iio_uri):
    """ad9361 driver attaches to the iio context and exposes attrs."""
    sdr = adi.ad9361(uri=iio_uri)
    try:
        assert sdr.ctx is not None
    finally:
        del sdr


def test_rx_buffer(iio_uri):
    """Capture a single RX buffer end-to-end."""
    sdr = adi.ad9361(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 1024
        data = sdr.rx()
        assert data is not None
        assert len(data) > 0
    finally:
        del sdr
