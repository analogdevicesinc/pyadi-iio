# Copyright (C) 2022-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4020(rx, context_manager):
    """AD4020 device"""

    _device_name = "ad4020"
    _rx_data_type = np.int32
    _complex_data = False
    _rx_channel_names = ["voltage0"]

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("ad4020")
        self._ctrl = self._ctx.find_device("ad4020")
        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """sample_rate: Only readable
        """
        return self._get_iio_dev_attr("sampling_frequency")
