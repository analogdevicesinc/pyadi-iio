"""Smoke test: open an AD9081 (mini2 = ZCU102 + AD9081) over IIO and read its context.

Run under the GH Actions HW workflow (places mini2 by manifest) or locally:
    pytest -v test/hw/test_ad9081_smoke.py --iio-uri-override ip:10.0.0.23
"""

from __future__ import annotations

import pytest

import adi


@pytest.mark.iio_hardware("ad9081")
def test_context_attrs(iio_uri):
    """The AD9081 driver enumerates context attrs (hw_model, etc.)."""
    sdr = adi.ad9081(uri=iio_uri)
    try:
        assert sdr.ctx is not None
        assert sdr.ctx.attrs, f"empty context attrs at {iio_uri}"
    finally:
        del sdr


@pytest.mark.iio_hardware("ad9081")
def test_rx_buffer(iio_uri):
    """Capture one small RX buffer end-to-end."""
    sdr = adi.ad9081(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 1024
        data = sdr.rx()
        assert data is not None
        # ad9081 RX is multi-channel: list of np arrays. At minimum non-empty.
        assert len(data) > 0
    finally:
        del sdr
