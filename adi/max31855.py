# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class max31855(rx, context_manager, attribute):
    """MAX31855 thermocouple device"""

    _device_name = "max31855"
    _rx_data_type = np.int16
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("maxim_thermocouple")

        if self._ctrl is None:
            raise Exception("No device found")

        self.temp_i = self._channel(self._ctrl, "i_temp")
        self.temp_t = self._channel(self._ctrl, "t_temp")
        self._rx_channel_names = ["t_temp", "i_temp"]
        rx.__init__(self)

    class _channel(attribute):
        """MAX31855 channel"""

        def __init__(self, ctrl, channel_name):
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
