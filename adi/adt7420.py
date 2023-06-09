# Copyright (C) 2022-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adt7420(attribute, context_manager):

    _device_name = "adt7420"

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception("ADT7420 device not found")

        self.temp = self._channel(self._ctrl, "temp")

    class _channel(attribute):
        """ADT7420 Channel"""

        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def temp_val(self):
            """ ADT7420 Channel Temperature Value """
            return self._get_iio_attr(self.name, "temp", False)

        @property
        def temp_max(self):
            """ ADT7420 Channel Max Temperature """
            return self._get_iio_attr(self.name, "temp_max", False)

        @temp_max.setter
        def temp_max(self, value):
            """ ADT7420 Channel Max Temperature """
            return self._set_iio_attr(self.name, "temp_max", False, value)

        @property
        def temp_min(self):
            """ ADT7420 Channel Min Temperature """
            return self._get_iio_attr(self.name, "temp_min", False)

        @temp_min.setter
        def temp_min(self, value):
            """ ADT7420 Channel Min Temperature """
            return self._set_iio_attr(self.name, "temp_min", False, value)

        @property
        def temp_crit(self):
            """ ADT7420 Channel Critical Temperature """
            return self._get_iio_attr(self.name, "temp_crit", False)

        @temp_crit.setter
        def temp_crit(self, value):
            """ ADT7420 Channel Critical Temperature """
            return self._set_iio_attr(self.name, "temp_crit", False, value)

        @property
        def temp_hyst(self):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._get_iio_attr(self.name, "temp_hyst", False)

        @temp_hyst.setter
        def temp_hyst(self, value):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._set_iio_attr(self.name, "temp_hyst", False, value)
