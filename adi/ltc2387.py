# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2387(rx, context_manager):

    """LTC2387 family devices"""

    _device_name = ""
    _rx_data_type = np.int32
    _complex_data = False
    _rx_channel_names = ["voltage"]

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ltc2387",
            "ltc2387-16",
            "ltc2387-18",
            "adaq23876",
            "adaq23878",
        ]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the xxx2387 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    break
                else:
                    index += 1

        rx.__init__(self)

    @property
    def sampling_frequency(self):

        """sample_rate: Sample rate in samples per second.
        Valid options are:
        Device's maximum sample rate (15000000 in the case of the LTC2387-18) and lower.
        Actual sample rates will be the master clock divided by an integer, for example,
        the CN0577 has a 120 MHz clock, so available sample rates will be:
        120 MHz / 8 = 15 Msps
        120 MHz / 9 = 13.333 Msps
        120 MHz / 10 = 12 Msps
        etc.
        """
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)
