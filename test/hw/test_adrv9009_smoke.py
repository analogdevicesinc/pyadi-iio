"""Smoke test: open an ADRV9009 (nemo = ZC706 + ADRV9009) over IIO.

Run under the GH Actions HW workflow (places nemo by manifest) or locally:
    pytest -v test/hw/test_adrv9009_smoke.py --iio-uri-override ip:<nemo-dut-ip>
"""

from __future__ import annotations

import pytest

import adi


@pytest.mark.iio_hardware("adrv9009")
def test_context_attrs(iio_uri):
    """The ADRV9009 driver enumerates context attrs."""
    sdr = adi.adrv9009(uri=iio_uri)
    try:
        assert sdr.ctx is not None
        assert sdr.ctx.attrs, f"empty context attrs at {iio_uri}"
    finally:
        del sdr


@pytest.mark.iio_hardware("adrv9009")
def test_rx_buffer(iio_uri):
    """Capture one small RX buffer end-to-end."""
    sdr = adi.adrv9009(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 1024
        data = sdr.rx()
        assert data is not None
        assert len(data) > 0
    finally:
        del sdr
