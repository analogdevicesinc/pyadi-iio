"""Smoke test: open a libiio context against a PlutoSDR and read its product ID.

Run under the new GH Actions HW workflow with LG_COORDINATOR + LG_PLACE
set (see conftest.py), or locally via:

    pytest -v test/hw/test_pluto_smoke.py --iio-uri-override ip:192.168.2.1
"""

from __future__ import annotations

import pytest

import adi


def test_open_context(iio_uri):
    """Pluto answers ctx.attrs and exposes its product ID."""
    sdr = adi.Pluto(uri=iio_uri)
    try:
        # `product_id` lives in libiio context attrs; raise if it's missing.
        ctx_attrs = dict(sdr.ctx.attrs)
        assert ctx_attrs, f"context attrs empty for {iio_uri}"
    finally:
        del sdr


def test_rx_buffer(iio_uri):
    """Capture a single RX buffer end-to-end."""
    sdr = adi.Pluto(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 1024
        data = sdr.rx()
        assert data is not None
        assert len(data) == sdr.rx_buffer_size
    finally:
        del sdr
