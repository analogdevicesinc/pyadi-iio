# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.device_base import rx_def


class ltc2387(rx_def):

    """LTC2387 family devices"""

    compatible_parts = [
        "ltc2387",
        "ltc2387-16",
        "ltc2387-18",
        "adaq23876",
        "adaq23878",
    ]
    _rx_data_type = np.int32
    _complex_data = False
    _rx_channel_names = ["voltage"]
    _device_name = ""
    _control_device_name = "ltc2387"
    _rx_data_device_name = "ltc2387"

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
