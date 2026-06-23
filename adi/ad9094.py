# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx
from adi.sync_start import sync_start


class ad9094(sync_start, rx, context_manager):
    """ AD9094 Quad ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3", "voltage4"]
    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._rxadc = self._ctx.find_device("axi-ad9094-hpc")
        rx.__init__(self)
