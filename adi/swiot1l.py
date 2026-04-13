# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import adi
from adi.attribute import attribute
from adi.context_manager import context_manager


class swiot1l(context_manager, attribute):

    _device_name = "swiot"

    """
    Interface for the no-os ADT75 IIO driver. Linux implements the lm75 driver
    using the hwmon framework instead (there is also the lm75 driver in
    no-os which exposes hwmon attributes).
    """

    class adt75_iio(context_manager, attribute):

        _device_name = ""

        def __init__(self, uri=""):
            context_manager.__init__(self, uri, self._device_name)
            self._ctrl = self._ctx.find_device("adt75")

        @property
        def raw(self):
            return self._get_iio_attr("temp", "raw", False)

        @property
        def scale(self):
            return self._get_iio_attr("temp", "scale", False)

        @property
        def offset(self):
            return self._get_iio_attr("temp", "offset", False)

        def __call__(self):
            """Utility function, returns deg. C"""
            return (self.raw * self.scale + self.offset) / 1000

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("swiot")

        if not self._ctrl:
            raise Exception("No swiot device found")

        if self.mode == "runtime":
            self.ad74413r = adi.ad74413r(uri)
            self.max14906 = adi.max14906(uri)
            self.adt75 = self.adt75_iio(uri)

    @property
    def mode(self):
        return self._get_iio_dev_attr_str("mode")

    @mode.setter
    def mode(self, value):
        self._set_iio_dev_attr_str("mode", value)

    @property
    def mode_available(self):
        return self._get_iio_dev_attr_str("mode_available")

    @property
    def identify(self):
        return self._get_iio_dev_attr_str("identify")

    @identify.setter
    def identify(self, value):
        self._set_iio_dev_attr_str("identify", value)

    @property
    def serial_id(self):
        return self._get_iio_dev_attr_str("serial_id")

    @property
    def ext_psu(self):
        return self._get_iio_dev_attr_str("ext_psu")

    @property
    def ch0_function(self):
        return self._get_iio_dev_attr_str("ch0_function")

    @ch0_function.setter
    def ch0_function(self, value):
        self._set_iio_dev_attr_str("ch0_function", value)

    @property
    def ch0_device(self):
        return self._get_iio_dev_attr_str("ch0_device")

    @ch0_device.setter
    def ch0_device(self, value):
        self._set_iio_dev_attr_str("ch0_device", value)

    @property
    def ch0_enable(self):
        return self._get_iio_dev_attr_str("ch0_enable")

    @ch0_enable.setter
    def ch0_enable(self, value):
        self._set_iio_dev_attr_str("ch0_enable", value)

    @property
    def ch0_function_available(self):
        return self._get_iio_dev_attr_str("ch0_function_available")

    @property
    def ch0_device_available(self):
        return self._get_iio_dev_attr_str("ch0_device_available")

    @property
    def ch1_function(self):
        return self._get_iio_dev_attr_str("ch1_function")

    @ch1_function.setter
    def ch1_function(self, value):
        self._set_iio_dev_attr_str("ch1_function", value)

    @property
    def ch1_device(self):
        return self._get_iio_dev_attr_str("ch1_device")

    @ch1_device.setter
    def ch1_device(self, value):
        self._set_iio_dev_attr_str("ch1_device", value)

    @property
    def ch1_enable(self):
        return self._get_iio_dev_attr_str("ch1_enable")

    @ch1_enable.setter
    def ch1_enable(self, value):
        self._set_iio_dev_attr_str("ch1_enable", value)

    @property
    def ch1_function_available(self):
        return self._get_iio_dev_attr_str("ch1_function_available")

    @property
    def ch1_device_available(self):
        return self._get_iio_dev_attr_str("ch1_device_available")

    @property
    def ch2_function(self):
        return self._get_iio_dev_attr_str("ch2_function")

    @ch2_function.setter
    def ch2_function(self, value):
        self._set_iio_dev_attr_str("ch2_function", value)

    @property
    def ch2_device(self):
        return self._get_iio_dev_attr_str("ch2_device")

    @ch2_device.setter
    def ch2_device(self, value):
        self._set_iio_dev_attr_str("ch2_device", value)

    @property
    def ch2_enable(self):
        return self._get_iio_dev_attr_str("ch2_enable")

    @ch2_enable.setter
    def ch2_enable(self, value):
        self._set_iio_dev_attr_str("ch2_enable", value)

    @property
    def ch2_function_available(self):
        return self._get_iio_dev_attr_str("ch2_function_available")

    @property
    def ch2_device_available(self):
        return self._get_iio_dev_attr_str("ch2_device_available")

    @property
    def ch3_function(self):
        return self._get_iio_dev_attr_str("ch3_function")

    @ch3_function.setter
    def ch3_function(self, value):
        self._set_iio_dev_attr_str("ch3_function", value)

    @property
    def ch3_device(self):
        return self._get_iio_dev_attr_str("ch3_device")

    @ch3_device.setter
    def ch3_device(self, value):
        self._set_iio_dev_attr_str("ch3_device", value)

    @property
    def ch3_enable(self):
        return self._get_iio_dev_attr_str("ch3_enable")

    @ch3_enable.setter
    def ch3_enable(self, value):
        self._set_iio_dev_attr_str("ch3_enable", value)

    @property
    def ch3_function_available(self):
        return self._get_iio_dev_attr_str("ch3_function_available")

    @property
    def ch3_device_available(self):
        return self._get_iio_dev_attr_str("ch3_device_available")

    def temp(self):
        return self.adt75()
