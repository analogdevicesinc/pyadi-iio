"""Smoke test: open an AD9371 (bq = ZC706 + ADRV9371) over IIO.

Run under the GH Actions HW workflow (places bq by manifest) or locally:
    pytest -v test/hw/test_ad9371_smoke.py --iio-uri-override ip:<bq-dut-ip>
"""

from __future__ import annotations

import pytest

import adi


@pytest.mark.iio_hardware("adrv9371")
def test_context_attrs(iio_uri):
    """The AD9371 driver enumerates context attrs."""
    sdr = adi.ad9371(uri=iio_uri)
    try:
        assert sdr.ctx is not None
        assert sdr.ctx.attrs, f"empty context attrs at {iio_uri}"
    finally:
        del sdr


@pytest.mark.iio_hardware("adrv9371")
def test_rx_buffer(iio_uri):
    """Capture one small RX buffer end-to-end."""
    sdr = adi.ad9371(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 1024
        data = sdr.rx()
        assert data is not None
        assert len(data) > 0
    finally:
        del sdr
