# Copyright (C) 2022-2025 Analog Devices, Inc.
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
      
        self.channel = []
        self._rx_channel_names = []

        for ch in self._ctrl.channels:
            name = ch._id

            self._rx_channel_names.append(name)
            self.channel.append(name)

            if name == "temp":
                # no-OS
                setattr(self, name, self.channel_temp(self._ctrl, name))
                self.temp = self.channel_temp(self._ctrl, "temp")
            elif name == "temp1":
                # Linux
                setattr(self, name, self.channel_temp1(self._ctrl, name))
                self.temp = self.channel_temp1(self._ctrl, "temp1")
            else:
                raise Exception(f"Unsupported: {name}")

    class channel_temp(attribute):
        """ADT7420 Channel for no-OS"""

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

    class channel_temp1(attribute):
        """ADT7420 Channel for Linux"""

        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def temp_val(self):
            """ ADT7420 Channel Temperature Value """
            return self._get_iio_attr(self.name, "input", False)

        @property
        def temp_max(self):
            """ ADT7420 Channel Max Temperature """
            return self._get_iio_attr(self.name, "max", False)

        @temp_max.setter
        def temp_max(self, value):
            """ ADT7420 Channel Max Temperature """
            return self._set_iio_attr(self.name, "max", False, value)

        @property
        def temp_min(self):
            """ ADT7420 Channel Min Temperature """
            return self._get_iio_attr(self.name, "min", False)

        @temp_min.setter
        def temp_min(self, value):
            """ ADT7420 Channel Min Temperature """
            return self._set_iio_attr(self.name, "min", False, value)

        @property
        def temp_crit(self):
            """ ADT7420 Channel Critical Temperature """
            return self._get_iio_attr(self.name, "crit", False)

        @temp_crit.setter
        def temp_crit(self, value):
            """ ADT7420 Channel Critical Temperature """
            return self._set_iio_attr(self.name, "crit", False, value)

        @property
        def temp_hyst(self):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._get_iio_attr(self.name, "max_hyst", False)

        @temp_hyst.setter
        def temp_hyst(self, value):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._set_iio_attr(self.name, "max_hyst", False, value)