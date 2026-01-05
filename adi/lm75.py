# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class lm75(context_manager, attribute):

    """ LM75 Temperature Sensor

    Parameters
    ----------
    uri: type=string
        Context URI. Default: Empty (auto-scan)
    device_index: type=integer
        Device index in contexts with multiple LM75 compatible devices. Default: 0
    returns:
        LM75 compatible device
    """

    _device_name = ""

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["lm75", "adt75"]

        self._ctrl = None
        index = 0
        # Select the device_index-th device from the lm75 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

    @property
    def update_interval(self):
        """Update Interval"""
        return self._get_iio_dev_attr("update_interval")

    def to_degrees(self, value):
        """Convert raw to degrees Celsius"""
        return value / 1000.0

    def to_millidegrees(self, value):
        """Convert degrees Celsius to millidegrees"""
        return int(value * 1000.0)

    @property
    def input(self):
        """LM75 temperature input value"""
        return self._get_iio_attr("temp1", "input", False)

    @property
    def max(self):
        """LM75 temperature max value"""
        return self._get_iio_attr("temp1", "max", False)

    @max.setter
    def max(self, value):
        """LM75 temperature max value"""
        return self._set_iio_attr("temp1", "max", False, value)

    @property
    def max_hyst(self):
        """LM75 max_hyst value"""
        return self._get_iio_attr("temp1", "max_hyst", False)

    @max_hyst.setter
    def max_hyst(self, value):
        """LM75 max_hyst value"""
        return self._set_iio_attr("temp1", "max_hyst", False, value)

    def __call__(self):
        """Utility function, returns deg. C"""
        return self.input / 1000
