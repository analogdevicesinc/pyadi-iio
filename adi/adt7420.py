# Copyright (C) 2022-2026 Analog Devices, Inc.
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
                # no-OS version
                chan = self.channel_temp(self._ctrl, name, is_linux=False)
            elif name == "temp1":
                # Linux version
                chan = self.channel_temp(self._ctrl, name, is_linux=True)
            else:
                raise Exception(f"Unsupported: {name}")

            setattr(self, name, chan)
            self.temp = chan

    class channel_temp(attribute):
        """ADT7420 Channel for no-OS"""

        def __init__(self, ctrl, channel_name, is_linux):
            self._ctrl = ctrl
            self.name = channel_name
            self.is_linux = is_linux

        @property
        def temp_val(self):
            """ ADT7420 Channel Temperature Value """
            pname = "input" if self.is_linux else "temp"
            return self._get_iio_attr(self.name, pname, False)

        @property
        def temp_max(self):
            """ ADT7420 Channel Max Temperature """
            pname = "max" if self.is_linux else "temp_max"
            return self._get_iio_attr(self.name, pname, False)

        @temp_max.setter
        def temp_max(self, value):
            """ ADT7420 Channel Max Temperature """
            pname = "max" if self.is_linux else "temp_max"
            return self._set_iio_attr(self.name, pname, False, value)

        @property
        def temp_min(self):
            """ ADT7420 Channel Min Temperature """
            pname = "min" if self.is_linux else "temp_min"
            return self._get_iio_attr(self.name, pname, False)

        @temp_min.setter
        def temp_min(self, value):
            """ ADT7420 Channel Min Temperature """
            pname = "min" if self.is_linux else "temp_min"
            return self._set_iio_attr(self.name, pname, False, value)

        @property
        def temp_crit(self):
            """ ADT7420 Channel Critical Temperature """
            pname = "crit" if self.is_linux else "temp_crit"
            return self._get_iio_attr(self.name, pname, False)

        @temp_crit.setter
        def temp_crit(self, value):
            """ ADT7420 Channel Critical Temperature """
            pname = "crit" if self.is_linux else "temp_crit"
            return self._set_iio_attr(self.name, pname, False, value)

        @property
        def temp_hyst(self):
            """ ADT7420 Channel Hysteresis Temperature """
            pname = "max_hyst" if self.is_linux else "temp_hyst"
            return self._get_iio_attr(self.name, pname, False)

        @temp_hyst.setter
        def temp_hyst(self, value):
            """ ADT7420 Channel Hysteresis Temperature """
            pname = "max_hyst" if self.is_linux else "temp_hyst"
            return self._set_iio_attr(self.name, pname, False, value)
