# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class max31855(rx_chan_comp, attribute):
    """MAX31855 thermocouple device"""

    _complex_data = False
    _device_name = "max31855"
    _rx_data_type = np.int16
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _control_device_name = "maxim_thermocouple"
    _rx_data_device_name = "maxim_thermocouple"
    _rx_channel_names = ["t_temp", "i_temp"]
    compatible_parts = ["max31855"]

    def __init__(self, uri=""):
        """Initialize the MAX31855 and retain its public temperature aliases."""
        super().__init__(uri=uri)
        self.temp_t = self.t_temp
        self.temp_i = self.i_temp

    class _channel(attribute):
        """MAX31855 channel"""

        def __init__(self, ctrl, channel_name):
            """Initialize a MAX31855 channel wrapper."""
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """MAX31855 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """MAX31855 channel scale value"""
            return self._get_iio_attr(self.name, "scale", False)

    _channel_def = _channel
