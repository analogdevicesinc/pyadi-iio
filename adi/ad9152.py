# Copyright (C) 2019-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import tx
from adi.sync_start import sync_start


class ad9152(tx, context_manager, sync_start):
    """ AD9152 High-Speed DAC """

    _complex_data = False
    _tx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._txdac = self._ctx.find_device("axi-ad9152-hpc")

        tx.__init__(self)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", True, value, self._txdac)
