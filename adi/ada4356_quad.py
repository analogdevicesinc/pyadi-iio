# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 synchronized capture with AXI TDD controller."""

from threading import Thread

import numpy as np

from adi.ada4355 import ada4355
from adi.context_manager import context_manager
from adi.tddn import tddn


class _tddn_quad(tddn):
    """tddn subclass that finds the TDD device by the name the
    adi,iio-fake-platform-device driver actually registers: 'adi-iio-fakedev'."""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, "")
        self._ctrl = self._ctx.find_device("adi-iio-fakedev")
        if not self._ctrl:
            raise Exception("TDD device 'adi-iio-fakedev' not found in context")
        self.channel = []
        for ch in self._ctrl.channels:
            self.channel.append(self._channel(self._ctrl, ch._id))


class _ada4356_ch_a(ada4355):
    _device_name = "ada4356-a"
    compatible_parts = ["ada4356-a"]


class _ada4356_ch_b(ada4355):
    _device_name = "ada4356-b"
    compatible_parts = ["ada4356-b"]


class _ada4356_ch_c(ada4355):
    _device_name = "ada4356-c"
    compatible_parts = ["ada4356-c"]


class _ada4356_ch_d(ada4355):
    _device_name = "ada4356-d"
    compatible_parts = ["ada4356-d"]


_CHANNEL_CLASSES = [_ada4356_ch_a, _ada4356_ch_b, _ada4356_ch_c, _ada4356_ch_d]
CHANNEL_LABELS = ["A", "B", "C", "D"]

TDD_CLOCK_HZ = 125_000_000

# Taps of the fractional-delay interpolator.  Half of this is unusable at each
# end of a shifted buffer, so the guard has to cover it as well as the draw.
_FRAC_TAPS = 32

# Spare samples captured on top of the requested buffer size, so rx() can slice
# the shift out and still return exactly rx_buffer_size.  _FRAC_TAPS of it pays
# for the interpolator edges; the rest is headroom for the divider draw.
ALIGN_GUARD = 64
MAX_DRAW_SPREAD = ALIGN_GUARD - _FRAC_TAPS


def _tone_phase(x, f_hz, fs):
    """Phase of the tone at f_hz, as in cos(2*pi*f_hz*n/fs + phase)."""
    n = np.arange(x.size)
    return np.angle(np.dot(x - x.mean(), np.exp(-2j * np.pi * f_hz * n / fs)))


def _frac_shift(x, samples):
    """Delay x by a fractional number of samples; negative advances it.

    Windowed-sinc interpolation, deliberately not the FFT phase-ramp trick: the
    buffer holds a non-integer number of cycles, so the FFT's implied wrap is a
    step discontinuity and shifting it rings at ~180 codes against ~6 codes of
    noise.  This is local instead, so the damage is confined to _FRAC_TAPS // 2
    samples at each end, which the guard region absorbs.
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


class ada4356_quad:
    """Quad ADA4356 with TDD-synchronized DMA capture.

    TDD channel mapping (set at block-design level):
      ch0  → trig_fmc_out  (external laser / trigger output)
      ch1  → DMA-A sync
      ch2  → DMA-B sync
      ch3  → DMA-C sync
      ch4  → DMA-D sync

    All four DMAs start capturing on the same TDD frame cycle so the
    sample streams are aligned to within one adc_clk period (8 ns).
    """

    def __init__(self, uri=""):
        self.ch_a = _ada4356_ch_a(uri=uri)
        self.ch_b = _ada4356_ch_b(uri=uri)
        self.ch_c = _ada4356_ch_c(uri=uri)
        self.ch_d = _ada4356_ch_d(uri=uri)
        self.channels = [self.ch_a, self.ch_b, self.ch_c, self.ch_d]

        self.tdd = _tddn_quad(uri=uri)

        self._align_delays = None
        self._align_frac = None
        self._rx_buffer_size = int(self.ch_a.rx_buffer_size)

    # ------------------------------------------------------------------
    # Buffer size — applied to all four channels at once
    # ------------------------------------------------------------------

    @property
    def rx_buffer_size(self):
        """Number of samples per capture per channel."""
        return self._rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self._rx_buffer_size = int(value)
        self._push_buffer_size()

    def _push_buffer_size(self):
        """Resize the per-channel buffers, guard region included.

        The old buffer has to be dropped first or the new size is silently
        ignored: it is built once on the first rx() and cached from then on.
        """
        n = self._rx_buffer_size
        if self._align_delays is not None:
            n += ALIGN_GUARD

        for ch in self.channels:
            ch.rx_destroy_buffer()
            ch._rx_stream = None  # libiio v1 caches the stream separately
            ch.rx_buffer_size = n

    # ------------------------------------------------------------------
    # Synchronized capture
    # ------------------------------------------------------------------

    def _rx_raw(self):
        """Capture one TDD-gated buffer per channel, with no realignment.

        Arms all four DMAs in parallel threads then waits for completion.
        The TDD controller gates each DMA via ch1..ch4, so all four start
        on the same clock edge.  Returns a list [A, B, C, D] of numpy arrays.

        The TDD must already be configured and enabled before calling
        this method.
        """
        # Without this the TDD pulses into DMAs that are not listening and the
        # four buffers start independently, giving hundreds of samples of skew.
        for ch in self.channels:
            ch._set_iio_dev_attr_str("sync_start_enable", "arm")

        results = [None] * 4
        errors = [None] * 4

        def _capture(idx, ch):
            try:
                results[idx] = ch.rx()
            except Exception as exc:
                errors[idx] = exc

        threads = [
            Thread(target=_capture, args=(i, ch))
            for i, ch in enumerate(self.channels)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for e in errors:
            if e:
                raise e

        return results

    def rx(self):
        """Capture one synchronized buffer from all four channels.

        Returns a list [A, B, C, D] of numpy arrays, each rx_buffer_size long.
        Once calibrate_alignment() has run, the per-boot offset is taken out
        here, so the four arrays share a sample index.
        """
        data = self._rx_raw()
        if self._align_delays is None:
            return data

        base = min(self._align_delays)
        n = self._rx_buffer_size
        frac = self._align_frac or [0.0] * len(data)
        edge = _FRAC_TAPS // 2

        out = []
        for x, d, fr in zip(data, self._align_delays, frac):
            if fr:
                x = _frac_shift(x, -fr)
            start = (d - base) + edge
            out.append(x[start : start + n])
        return out

    # ------------------------------------------------------------------
    # Channel alignment
    # ------------------------------------------------------------------
    # Front-end transimpedance
    # ------------------------------------------------------------------

    @property
    def gain_mode_available(self):
        """Transimpedance settings the driver accepts, e.g. ['133k', '11k', '4k54']."""
        return (
            self.ch_a._get_iio_attr_str("voltage0", "gain_mode_available", False)
            .strip()
            .split()
        )

    @property
    def gain_mode(self):
        """Per-channel transimpedance, as a dict keyed by A..D."""
        return {
            label: ch._get_iio_attr_str("voltage0", "gain_mode", False).strip()
            for label, ch in zip(CHANNEL_LABELS, self.channels)
        }

    @gain_mode.setter
    def gain_mode(self, value):
        available = self.gain_mode_available
        if value not in available:
            raise ValueError(f"gain_mode must be one of {available}, got {value!r}")

        for ch in self.channels:
            ch._set_iio_attr("voltage0", "gain_mode", False, value)

        # Transimpedance sets the front-end propagation delay -- measured at 50 ns
        # between 133k and 11k on one channel -- so any prior calibration is stale.
        self._reset_alignment()
        self._push_buffer_size()

    # ------------------------------------------------------------------

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

    def calibrate_alignment(self, tone_hz, verbose=True, subsample=True):
        """Lock the four channels onto a common sample index, for this boot.

        Needs the same tone on all four inputs; J11 already feeds all of them.

        The FPGA re-draws each channel's BUFR /4 divider phase every time it is
        configured, so B/C/D come up a whole number of samples behind A and the
        draw is different on every boot.  TDD only lines the DMA starts up to
        one adc_clk period, so it cannot see this, and re-pulsing the shared
        SERDES reset was measured to leave 8.8-16.8 ns of spread.  Measuring the
        draw once and shifting the buffers is deterministic instead.

        With subsample=True the fixed analog delay is taken out as well, by
        phase-rotating the buffer.  That also makes the result independent of how
        the measured delay splits into integer and fraction, which matters when a
        channel lands near a half sample: at 4.54k/200R channel C sits at +0.49,
        so integer-only rounding can flip between boots and swing the corrected
        skew by a whole 8 ns sample.  Pass subsample=False to shift by whole
        samples only, leaving the data untouched by any filtering.

        Call this once per boot, after the TDD is enabled and the tone is
        applied.
        """
        self._align_delays = [0] * len(self.channels)
        self._push_buffer_size()

        raw = [x.astype(np.float64) for x in self._rx_raw()]
        fs = self.sampling_frequency
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

        if verbose:
            self._print_alignment(f0, fs, delays, offsets, residual, subsample)

        return {
            "tone_hz": f0,
            "delay_samples": dict(zip(CHANNEL_LABELS, delays)),
            "removed_samples": dict(zip(CHANNEL_LABELS, offsets)),
            "residual_samples": dict(zip(CHANNEL_LABELS, residual)),
            "subsample": subsample,
        }

    def _reset_alignment(self):
        self._align_delays = None
        self._align_frac = None
        self._push_buffer_size()

    @staticmethod
    def _print_alignment(f0, fs, delays, offsets, residual, subsample):
        print(f"\n=== Channel alignment (tone {f0 / 1e3:.3f} kHz) ===")
        print(
            f"{'Ch':>3}  {'measured':>10}  {'whole':>7}  {'frac':>8}  "
            f"{'left over':>10}"
        )
        print(
            f"{'':>3}  {'(samp)':>10}  {'(samp)':>7}  {'(samp)':>8}  {'(ns)':>10}"
        )
        for label, v, k, r in zip(CHANNEL_LABELS, delays, offsets, residual):
            left = 0.0 if subsample else r
            print(
                f"{label:>3}  {v:>10.4f}  {k:>7d}  {r:>8.4f}  "
                f"{left / fs * 1e9:>10.2f}"
            )

        if subsample:
            print("  whole samples sliced out, fraction interpolated out")
            print("  -> channels share a time base; the split above does not matter")
        else:
            floor = max(residual) - min(residual)
            print(
                f"  integer draw removed; {floor:.4f} samp "
                f"({floor / fs * 1e9:.2f} ns) of analog skew is left"
            )
            if max(abs(r) for r in residual) > 0.4:
                print(
                    "  *** a channel sits near half a sample, so the rounding can"
                    "\n  *** flip between boots and move the result by 8 ns."
                    "\n  *** use subsample=True to make this irrelevant"
                )
        print("  this holds until the FPGA is reconfigured or the driver re-probes")

    # ------------------------------------------------------------------
    # Sampling frequency
    # ------------------------------------------------------------------

    @property
    def sampling_frequency(self):
        """ADC sample rate (Hz), read from channel A."""
        return float(self.ch_a.sampling_frequency)
