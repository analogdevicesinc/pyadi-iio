# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 synchronized capture with AXI TDD controller."""

from threading import Thread

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

    # ------------------------------------------------------------------
    # Buffer size — applied to all four channels at once
    # ------------------------------------------------------------------

    @property
    def rx_buffer_size(self):
        """Number of samples per capture per channel."""
        return self.ch_a.rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        for ch in self.channels:
            ch.rx_buffer_size = value

    # ------------------------------------------------------------------
    # Synchronized capture
    # ------------------------------------------------------------------

    def rx(self):
        """Capture one synchronized buffer from all four channels.

        Arms all four DMAs in parallel threads then waits for completion.
        The TDD controller gates each DMA via ch1..ch4, so all four start
        on the same clock edge.  Returns a list [A, B, C, D] of numpy arrays.

        The TDD must already be configured and enabled before calling
        this method.
        """
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

    # ------------------------------------------------------------------
    # Sampling frequency
    # ------------------------------------------------------------------

    @property
    def sampling_frequency(self):
        """ADC sample rate (Hz), read from channel A."""
        return float(self.ch_a.sampling_frequency)
