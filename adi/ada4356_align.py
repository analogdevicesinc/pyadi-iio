# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Per-boot sample alignment of the four Quad ADA4356 channels."""

import logging

import numpy as np

logger = logging.getLogger(__name__)

CHANNEL_LABELS = ["A", "B", "C", "D"]

# Interpolator taps; half are unusable at each end of a shifted buffer.
_FRAC_TAPS = 32

# Extra samples per capture so rx() can slice out the shift: FIR edges + draw.
ALIGN_GUARD = 64
MAX_DRAW_SPREAD = ALIGN_GUARD - _FRAC_TAPS


def _tone_phase(x, f_hz, fs):
    """Phase of the tone at f_hz, as in cos(2*pi*f_hz*n/fs + phase).

    parameters:
        x: type=numpy.array
            Samples of one channel.
        f_hz: type=float
            Tone frequency in Hz.
        fs: type=float
            Sample rate in Hz.
    returns: type=float
        Phase in radians, -pi..pi.
    """
    n = np.arange(x.size)
    return np.angle(np.dot(x - x.mean(), np.exp(-2j * np.pi * f_hz * n / fs)))


def _frac_shift(x, samples):
    """Delay x by a fractional number of samples; negative advances it.

    Windowed-sinc interpolation, deliberately not the FFT phase-ramp trick: the
    buffer holds a non-integer number of cycles, so the FFT's implied wrap is a
    step discontinuity and shifting it rings at ~180 codes against ~6 codes of
    noise.  This is local instead, so the damage is confined to _FRAC_TAPS // 2
    samples at each end, which the guard region absorbs.

    parameters:
        x: type=numpy.array
            Samples of one channel.
        samples: type=float
            Delay in samples; negative advances.
    returns: type=numpy.array
        The shifted samples, same length as x.
    """
    half = _FRAC_TAPS // 2
    m = np.arange(-half, half + 1) - samples
    h = np.sinc(m) * np.kaiser(_FRAC_TAPS + 1, 8.0)
    h /= h.sum()
    return np.convolve(x, h, mode="same")


def _estimate_tone_hz(x, f_req, fs):
    """Refine the generator frequency near f_req by maximising the windowed DFT.

    Bounded to +-2 bins on purpose: an unconstrained peak search locks onto the
    ~0.89 MHz board spur and returns a stable, completely wrong answer.

    parameters:
        x: type=numpy.array
            Samples of one channel.
        f_req: type=float
            Frequency the generator was set to, in Hz.
        fs: type=float
            Sample rate in Hz.
    returns: type=float
        Refined tone frequency in Hz.
    """
    n = np.arange(x.size)
    xw = (x - x.mean()) * np.hanning(x.size)
    bin_hz = fs / x.size
    lo, hi = f_req - 2 * bin_hz, f_req + 2 * bin_hz

    grid = np.array([float(f_req)])
    idx = 0
    for _ in range(3):
        grid = np.linspace(max(lo, bin_hz), hi, 41)
        mag = [abs(np.dot(xw, np.exp(-2j * np.pi * f * n / fs))) for f in grid]
        idx = int(np.argmax(mag))
        step = grid[1] - grid[0]
        lo, hi = grid[idx] - step, grid[idx] + step

    return float(grid[idx])


class _ada4356_alignment:
    """Alignment calibration and correction, mixed into ada4356_quad.

    The host class provides channels, _rx_raw(), _push_buffer_size(),
    sampling_frequency, _rx_buffer_size, and initialises _align_delays and
    _align_frac to None.
    """

    def apply_alignment(self, data, correct=True):
        """Trim raw buffers to rx_buffer_size, optionally removing the draw.

        With correct=False every channel is sliced at the same offset, so the
        per-boot draw is left in and the channels stay comparable.

        parameters:
            data: type=list of numpy.array
                Raw capture, [A, B, C, D], as returned by rx_raw().
            correct: type=bool
                Remove the measured offsets; False only trims.
        returns: type=list of numpy.array
            One array per channel, each rx_buffer_size long.
        """
        n = self._rx_buffer_size
        edge = _FRAC_TAPS // 2

        if self._align_delays is None:
            return [np.asarray(x)[:n] for x in data]

        if not correct:
            return [np.asarray(x)[edge : edge + n] for x in data]

        base = min(self._align_delays)
        frac = self._align_frac or [0.0] * len(data)

        out = []
        for x, d, fr in zip(data, self._align_delays, frac):
            x = np.asarray(x, dtype=np.float64)
            if fr:
                x = _frac_shift(x, -fr)
            start = (d - base) + edge
            out.append(x[start : start + n])
        return out

    @property
    def alignment(self):
        """Integer sample offsets being removed, or None if not calibrated."""
        if self._align_delays is None:
            return None
        return dict(zip(CHANNEL_LABELS, self._align_delays))

    def set_alignment(self, offsets, frac=None):
        """Apply a previously measured alignment without re-measuring.

        Exists so a calibration taken under one set of conditions can be checked
        against a capture taken under another -- a different tone, say.  Verifying
        with the same tone the correction was fitted to cannot fail, so it proves
        very little on its own.

        parameters:
            offsets: type=list[int]
                Whole-sample offsets for A..D, e.g. the 'removed_samples'
                values from calibrate_alignment().
            frac: type=list[float]
                Optional fractional residuals for A..D, e.g. the
                'residual_samples' values.  None shifts by whole samples only.

        Raises:
            ValueError: If the lists have the wrong length, or the offsets
                span more than MAX_DRAW_SPREAD samples.
        """
        offsets = [int(v) for v in offsets]
        if len(offsets) != len(self.channels):
            raise ValueError(f"expected {len(self.channels)} offsets")
        if frac is not None:
            frac = [float(v) for v in frac]
            if len(frac) != len(offsets):
                raise ValueError("frac must match offsets in length")

        spread = max(offsets) - min(offsets)
        if spread > MAX_DRAW_SPREAD:
            raise ValueError(
                f"offsets span {spread} samples, beyond the {MAX_DRAW_SPREAD}-sample guard"
            )

        self._align_delays = offsets
        self._align_frac = frac
        self._push_buffer_size()

    def calibrate_alignment(self, tone_hz, subsample=True):
        """Lock the four channels onto a common sample index, for this boot.

        Needs the same tone on all four inputs; J11 already feeds all of them.

        The FPGA re-draws each channel's BUFR /4 divider phase every time it is
        configured, so B/C/D come up a whole number of samples behind A and the
        draw is different on every boot.  TDD only lines the DMA starts up to
        one adc_clk period, so it cannot see this, and re-pulsing the shared
        SERDES reset was measured to leave 8.8-16.8 ns of spread.  Measuring the
        draw once and shifting the buffers is deterministic instead.

        With subsample=True the fixed analog delay is taken out as well, by
        interpolating the buffer (the windowed-sinc FIR in _frac_shift()).  That
        also makes the result independent of how the measured delay splits into
        integer and fraction, which matters when a channel lands near a half
        sample: at 4.54k/200R channel C sits at +0.49, so integer-only rounding
        can flip between boots and swing the corrected skew by a whole 8 ns
        sample.  Pass subsample=False to shift by whole samples only, leaving the
        data untouched by any filtering.

        Call this once per boot, after the TDD is enabled and the tone is
        applied.

        parameters:
            tone_hz: type=float
                Frequency of the tone on all four inputs, in Hz; refined from
                the capture within +-2 FFT bins.
            subsample: type=bool
                Also interpolate out the fractional delay.  False shifts by
                whole samples only.
        returns: type=dict
            'tone_hz' (refined frequency), 'delay_samples',
            'removed_samples' and 'residual_samples' (each a dict keyed
            A..D), and 'subsample'.

        Raises:
            RuntimeError: If a channel carries no tone, or the channels span
                more than MAX_DRAW_SPREAD samples.
            ExceptionGroup: If the capture failed on one or more channels.
        """
        self._align_delays = [0] * len(self.channels)
        self._push_buffer_size()

        try:
            raw = [x.astype(np.float64) for x in self._rx_raw()]
            fs = self.sampling_frequency
        except Exception:
            # Otherwise the zero placeholder above passes for a calibration.
            self._reset_alignment()
            raise
        f0 = _estimate_tone_hz(raw[0], float(tone_hz), fs)
        samples_per_cycle = fs / f0

        ref = _tone_phase(raw[0], f0, fs)
        delays = []
        for label, x in zip(CHANNEL_LABELS, raw):
            if np.std(x) < 10.0:
                self._reset_alignment()
                raise RuntimeError(
                    f"channel {label} carries no tone (rms {np.std(x):.1f} codes); "
                    "all four inputs need the same signal to be aligned"
                )
            # A delay of s samples retards the phase by 2*pi*f0*s/fs.
            dphi = (ref - _tone_phase(x, f0, fs) + np.pi) % (2 * np.pi) - np.pi
            delays.append(dphi / (2 * np.pi) * samples_per_cycle)

        offsets = [int(round(v)) for v in delays]
        residual = [v - k for v, k in zip(delays, offsets)]

        spread = max(offsets) - min(offsets)
        if spread > MAX_DRAW_SPREAD:
            self._reset_alignment()
            raise RuntimeError(
                f"channels span {spread} samples, beyond the {MAX_DRAW_SPREAD}-sample "
                "guard; that is a gross misalignment, not a divider phase draw"
            )

        self._align_delays = offsets
        self._align_frac = residual if subsample else None
        self._push_buffer_size()

        if not subsample and max(abs(r) for r in residual) > 0.4:
            # Integer rounding near half a sample can flip between boots: 8 ns.
            logger.warning(
                "a channel sits near half a sample, so whole-sample alignment can "
                "move by 8 ns between boots; use subsample=True to avoid this"
            )

        return {
            "tone_hz": f0,
            "delay_samples": dict(zip(CHANNEL_LABELS, delays)),
            "removed_samples": dict(zip(CHANNEL_LABELS, offsets)),
            "residual_samples": dict(zip(CHANNEL_LABELS, residual)),
            "subsample": subsample,
        }

    def _reset_alignment(self):
        """Drop the calibration and shrink the buffers back to rx_buffer_size."""
        self._align_delays = None
        self._align_frac = None
        self._push_buffer_size()
