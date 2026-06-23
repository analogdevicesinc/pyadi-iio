# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import List

from adi.ad9081 import _sortconv
from adi.context_manager import context_manager
from adi.rx_tx import tx
from adi.sync_start import sync_start


class ad9172(tx, context_manager, sync_start):
    """AD9172 High-Speed DAC"""

    _complex_data = True
    _tx_channel_names: List[str] = []
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._txdac = self._ctx.find_device("axi-ad9172-hpc")
        if not self._txdac:
            raise RuntimeError("Could not find axi-ad9172-hpc")

        self._tx_channel_names = []
        for chan in self._txdac.channels:
            if (
                hasattr(chan, "scan_element")
                and chan.scan_element
                and chan.id not in self._tx_channel_names
            ):
                self._tx_channel_names.append(chan.id)

        self._tx_channel_names = _sortconv(self._tx_channel_names, complex=True)

        tx.__init__(self)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate TX path in samples per second"""
        return self._get_iio_attr(
            self._tx_channel_names[0], "sampling_frequency", True, self._txdac
        )
