"""Smoke test: open an AD9371 / ADRV9371 over IIO.

Discovered by labgrid-plugins hw-matrix.yml@v2 — any coordinator place
tagged ``daughter-board=adrv9371`` (or the legacy ``ad9371`` alias)
will fan a shard of this file out.

Local manual run:
    pytest -v test/hw/test_ad9371_smoke.py --iio-uri-override ip:<bq-dut-ip>
"""

from __future__ import annotations

import adi
import pytest


@pytest.mark.iio_hardware(["adrv9371", "ad9371"])
def test_context_attrs(iio_uri):
    """The AD9371 driver enumerates context attrs."""
    sdr = adi.ad9371(uri=iio_uri)
    try:
        assert sdr.ctx is not None
        assert sdr.ctx.attrs, f"empty context attrs at {iio_uri}"
    finally:
        del sdr


@pytest.mark.iio_hardware(["adrv9371", "ad9371"])
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
