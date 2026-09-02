"""Smoke test: FMCDAQ3 (nuc = VCU118 + FMCDAQ3) over IIO, DAC->ADC loopback.

DAQ3 = adi.DAQ3(ad9152 DAC + ad9680 ADC), both non-complex. The DAC and ADC
are loop-coupled on the FMCDAQ3 card, so a DDS tone driven out the AD9152
appears on the AD9680 RX. We assert the tone shows up as a clear FFT peak.

Run under the GH Actions HW workflow (places nuc by board tag daq3) or locally:
    pytest -v test/hw/test_daq3_smoke.py --iio-uri-override ip:<nuc-dut-ip>
"""

from __future__ import annotations

import numpy as np
import pytest

import adi


@pytest.mark.iio_hardware("daq3")
def test_context_attrs(iio_uri):
    """The DAQ3 driver opens and enumerates context attrs."""
    sdr = adi.DAQ3(uri=iio_uri)
    try:
        assert sdr.ctx is not None
        assert sdr.ctx.attrs, f"empty context attrs at {iio_uri}"
        # Both converters present on the context.
        assert sdr._txdac is not None
        assert sdr._rxadc is not None
    finally:
        del sdr


@pytest.mark.iio_hardware("daq3")
def test_rx_buffer(iio_uri):
    """Capture one small RX buffer end-to-end."""
    sdr = adi.DAQ3(uri=iio_uri)
    try:
        sdr.rx_buffer_size = 2 ** 12
        data = sdr.rx()
        assert data is not None
        # ad9680 RX is multi-channel real data: list of np arrays.
        assert len(data) > 0
        assert len(np.asarray(data[0])) == sdr.rx_buffer_size
    finally:
        del sdr


@pytest.mark.iio_hardware("daq3")
def test_dds_loopback_tone(iio_uri):
    """Drive a DDS tone out the AD9152 DAC, see it on the AD9680 ADC via FFT."""
    sdr = adi.DAQ3(uri=iio_uri)
    try:
        # ad9680 RX rate: read the ADC channel's sampling_frequency directly.
        # ad9680 exposes no rx_sample_rate property, so go through _rxadc.
        fs = int(sdr._get_iio_attr("voltage0", "sampling_frequency", False, sdr._rxadc))
        sdr.rx_buffer_size = 2 ** 14
        sdr.rx_enabled_channels = [0]

        # Tone at ~fs/8, well inside the first Nyquist zone, mid scale.
        tone_hz = fs // 8
        sdr.dds_single_tone(tone_hz, 0.5, channel=0)

        # Flush a couple buffers so the DDS tone is steady-state.
        data = None
        for _ in range(3):
            data = sdr.rx()

        x = np.asarray(data[0] if isinstance(data, list) else data, dtype=float)
        x = x - np.mean(x)
        win = np.hanning(len(x))
        spec = np.abs(np.fft.rfft(x * win))
        freqs = np.fft.rfftfreq(len(x), d=1.0 / fs)

        # Ignore DC bin; the peak should land near the commanded tone.
        spec[0] = 0.0
        peak_bin = int(np.argmax(spec))
        peak_hz = freqs[peak_bin]

        # Peak must be a real tone (well above the median noise floor) ...
        noise = np.median(spec[spec > 0])
        tone_msg = f"no dominant tone: peak={spec[peak_bin]:.1f} floor~{noise:.1f}"
        assert spec[peak_bin] > 10 * noise, tone_msg
        # ... and within ~5% of the commanded frequency.
        freq_msg = f"peak {peak_hz:.0f} Hz far from commanded {tone_hz} Hz"
        assert abs(peak_hz - tone_hz) < 0.05 * fs, freq_msg
    finally:
        try:
            sdr.disable_dds()
        except Exception:
            pass
        del sdr
