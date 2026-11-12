# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 synchronized capture with AXI TDD controller."""

from threading import Thread

import numpy as np

from adi.ada4355 import ada4355
from adi.ada4356_align import ALIGN_GUARD, CHANNEL_LABELS, _ada4356_alignment
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

# Written via debugfs; SDO readback is broken (0xFF), so state is what we last wrote.
AD9517_DEVICE = "ad9517-4"
# OUT4..7 = ADC A..D (A and D confirmed on hardware).
_AD9517_OUT_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
_AD9517_DELAY_BYPASS = 0xA0  # + 3 * index; ramp at +1, fraction at +2
# Divider 2 -> OUT4/5 (A+B), divider 3 -> OUT6/7 (C+D).
_AD9517_PHASE_REG = {"AB": 0x19A, "CD": 0x19F}
_AD9517_SOFT_SYNC = 0x230
AD9517_DEFAULT_RAMP = 0x39  # the only ramp characterised: 0.040-0.043 ns/LSB
AD9517_MAX_FRACTION = 47
# Fractions 44 and 47 at ramp 0x39 froze the board; do not raise the cap
# without measuring above fraction 41.
AD9517_DELAY_SAFE_PS = 2200
AD9517_DELAY_OFFSET_PS = 460  # datasheet; measured 380-410 ps


def ad9517_delay_estimate_ps(ramp, fraction):
    """Fine-delay estimate for an AD9517 output, from the datasheet formula."""
    caps = 4 - bin((ramp >> 3) & 0x7).count("1")
    iramp_ua = 200 * ((ramp & 0x7) + 1)
    range_ps = 265720 * (caps + 3) / iramp_ua
    return range_ps * fraction / 63 + AD9517_DELAY_OFFSET_PS


class ada4356_quad(_ada4356_alignment):
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
        self._clk_delay = {}
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

        Raises:
            ExceptionGroup: one sub-exception per channel whose rx() failed,
                each with its original type (e.g. TimeoutError).
        """
        # Unarmed DMAs start independently: hundreds of samples of skew.
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
            Thread(target=_capture, args=(i, ch)) for i, ch in enumerate(self.channels)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        failed = [
            (label, e) for label, e in zip(CHANNEL_LABELS, errors) if e is not None
        ]
        if failed:
            # Raise them all: the first alone would hide that, say, B and D both
            # timed out on the same missing TDD pulse.
            raise ExceptionGroup(
                "rx failed on channel " + ", ".join(label for label, _ in failed),
                [e for _, e in failed],
            )

        return results

    def rx_raw(self):
        """One synchronized capture with no alignment applied.

        Pair with apply_alignment() to get a corrected/uncorrected A/B from the
        *same* acquisition.  Two separate rx() calls only compare if the
        stimulus repeats shot to shot, which a free-running generator does not.
        """
        return self._rx_raw()

    def rx(self):
        """Capture one synchronized buffer from all four channels.

        Returns a list [A, B, C, D] of numpy arrays, each rx_buffer_size long.
        Once calibrate_alignment() has run, the per-boot offset is taken out
        here, so the four arrays share a sample index.
        """
        return self.apply_alignment(self._rx_raw())

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

        # Transimpedance moves the front-end delay (50 ns, 133k vs 11k).
        self._reset_alignment()
        self._push_buffer_size()

    @property
    def filter_mode_available(self):
        """FREQ_SEL settings the driver accepts, named after the pin level."""
        return (
            self.ch_a._get_iio_attr_str("voltage0", "filter_mode_available", False)
            .strip()
            .split()
        )

    @property
    def filter_mode(self):
        """Per-channel FREQ_SEL filter, as a dict keyed by A..D."""
        return {
            label: ch._get_iio_attr_str("voltage0", "filter_mode", False).strip()
            for label, ch in zip(CHANNEL_LABELS, self.channels)
        }

    @filter_mode.setter
    def filter_mode(self, value):
        available = self.filter_mode_available
        if value not in available:
            raise ValueError(f"filter_mode must be one of {available}, got {value!r}")

        for ch in self.channels:
            ch._set_iio_attr("voltage0", "filter_mode", False, value)

        # Group-delay effect not measured, so do not trust the old calibration.
        self._reset_alignment()
        self._push_buffer_size()

    # ------------------------------------------------------------------
    # AD9517 per-ADC sample-clock delay / phase
    # ------------------------------------------------------------------
    # Moves the analog sampling instant and that ADC's FPGA capture clock together.
    # A constant shift may also pin the per-boot whole-sample draw (untested).

    def _ad9517(self):
        dev = self.ch_a._ctx.find_device(AD9517_DEVICE)
        if dev is None:
            raise RuntimeError(f"{AD9517_DEVICE} not found in context")
        return dev

    def _ad9517_write(self, reg, val):
        self._ad9517().reg_write(reg, val)

    @property
    def clock_delay(self):
        """Fine delay last written per channel by this object (None = never written).

        Each entry is {'enabled', 'ramp', 'fraction', 'estimate_ps'}. A reboot
        restores the firmware state: all bypassed.
        """
        return {label: self._clk_delay.get(label) for label in CHANNEL_LABELS}

    def set_clock_delay(self, channel, fraction, ramp=AD9517_DEFAULT_RAMP, enable=None):
        """Delay one ADC's sample clock with the AD9517 fine delay (adds delay only).

        enable defaults to fraction > 0; enable=True with fraction 0 routes the clock
        through the delay block, which alone adds ~0.4-0.5 ns (measured 2026-10-19).
        Raises ValueError above AD9517_DELAY_SAFE_PS.
        A delayed channel's tone skew goes up (it reads earlier); its LiDAR
        'd vs A' goes down.
        """
        label = channel.upper()
        if label not in _AD9517_OUT_INDEX:
            raise ValueError(
                f"channel must be one of {CHANNEL_LABELS}, got {channel!r}"
            )
        fraction, ramp = int(fraction), int(ramp)
        if not 0 <= ramp <= 0x3F:
            raise ValueError(f"ramp must be 0..0x3F, got {ramp:#x}")
        if not 0 <= fraction <= AD9517_MAX_FRACTION:
            raise ValueError(
                f"fraction must be 0..{AD9517_MAX_FRACTION}, got {fraction}"
            )
        est = ad9517_delay_estimate_ps(ramp, fraction)
        if est > AD9517_DELAY_SAFE_PS:
            raise ValueError(
                f"ramp {ramp:#04x} fraction {fraction} ~{est:.0f} ps exceeds the "
                f"{AD9517_DELAY_SAFE_PS} ps cap (fraction >= 44 froze the board)"
            )

        enable = bool(fraction) if enable is None else bool(enable)
        base = _AD9517_DELAY_BYPASS + 3 * _AD9517_OUT_INDEX[label]
        # Bypass first, so no intermediate ramp/fraction pair can exceed the cap.
        self._ad9517_write(base, 1)
        self._ad9517_write(base + 1, ramp)
        self._ad9517_write(base + 2, fraction)
        if enable:
            self._ad9517_write(base, 0)

        self._clk_delay[label] = {
            "enabled": enable,
            "ramp": ramp,
            "fraction": fraction,
            "estimate_ps": est if enable else 0.0,
        }
        self._reset_alignment()

    def bypass_clock_delays(self):
        """Put all four ADC clocks back on the undelayed path (firmware state)."""
        for label in CHANNEL_LABELS:
            self.set_clock_delay(label, 0)

    def set_clock_phase(self, pair, offset, sync=True):
        """Divider phase offset for a clock pair: 'AB' (OUT4/5) or 'CD' (OUT6/7).

        One step = one 250 MHz divider-input cycle = 4 ns. Takes effect only on a
        sync, which restarts all four ADC clocks -- check 'frame align:' in dmesg
        afterwards.
        """
        pair = pair.upper()
        if pair not in _AD9517_PHASE_REG:
            raise ValueError(f"pair must be 'AB' or 'CD', got {pair!r}")
        offset = int(offset)
        if not 0 <= offset <= 15:
            raise ValueError(f"offset must be 0..15, got {offset}")
        # .2 stage is bypassed by the firmware, so its PO[7:4] stays 0.
        self._ad9517_write(_AD9517_PHASE_REG[pair], offset)
        if sync:
            self.clock_sync()

    def clock_sync(self):
        """AD9517 soft sync: realigns every divider, briefly stopping all ADC clocks."""
        self._ad9517_write(_AD9517_SOFT_SYNC, 1)
        self._ad9517_write(_AD9517_SOFT_SYNC, 0)
        self._reset_alignment()

    # ------------------------------------------------------------------
    # Sampling frequency
    # ------------------------------------------------------------------

    @property
    def sampling_frequency(self):
        """ADC sample rate (Hz), read from channel A."""
        return float(self.ch_a.sampling_frequency)
