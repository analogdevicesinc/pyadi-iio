# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""ADA4356 Dual-Board Synchronized System"""

from threading import Thread

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx
from adi.tddn import tddn


class _ada4356_board(rx, context_manager, attribute):
    """Single ADA4356 board — selects IIO device by exact name.

    The AXI ADC devices appear in the IIO context as 'axi-ada4356-0'
    and 'axi-ada4356-1', not 'ada4355', so this class finds them directly.
    """

    _complex_data = False
    _device_name = ""

    def __init__(self, uri, device_name):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device(device_name)
        if not self._ctrl:
            raise Exception(f"Device '{device_name}' not found in context")
        self._rxadc = self._ctrl
        self._rx_channel_names = [ch._id for ch in self._ctrl.channels]
        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """ADC sample rate in Hz."""
        return float(self._get_iio_dev_attr("sampling_frequency"))


class ada4356_dual:
    """Dual ADA4356 System with TDD-synchronized DMA capture.

    board0 — FMC HPC0 (axi-ada4356-0)
    board1 — FMC HPC1 (axi-ada4356-1)
    TDD channel 1 gates DMA0, TDD channel 2 gates DMA1.
    Both channels fire on the same clock cycle so both DMAs start together.
    """

    TDD_CLOCK_HZ = 125_000_000

    def __init__(self, uri=""):
        self.board0 = _ada4356_board(uri, "axi-ada4356-0")
        self.board1 = _ada4356_board(uri, "axi-ada4356-1")
        self.tdd = tddn(uri)

    def rx_synced(self):
        """Arm both DMAs concurrently and block until TDD fires.

        Returns (data0, data1) as numpy int16 arrays.
        """
        results = [None, None]
        errors = [None, None]

        def capture(board, idx):
            try:
                results[idx] = board.rx()
            except Exception as exc:
                errors[idx] = exc

        threads = [
            Thread(target=capture, args=(self.board0, 0)),
            Thread(target=capture, args=(self.board1, 1)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for e in errors:
            if e:
                raise e

        return results[0], results[1]
