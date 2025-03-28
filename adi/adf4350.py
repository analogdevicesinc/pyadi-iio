# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4350(attribute, context_manager):
    """ADF4350 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4350
    """

    _device_name = ""

    def __init__(self, uri="", device_name="adf4350"):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4350 device not found")

    @property
    def frequency_altvolt0(self):
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency_altvolt0.setter
    def frequency_altvolt0(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def frequency_resolution_altvolt0(self):
        return self._get_iio_attr(
            "altvoltage0", "frequency_resolution", True, self._ctrl
        )

    @frequency_resolution_altvolt0.setter
    def frequency_resolution_altvolt0(self, value):
        self._set_iio_attr(
            "altvoltage0", "frequency_resolution", True, value, self._ctrl
        )

    @property
    def refin_frequency_altvolt0(self):
        return self._get_iio_attr("altvoltage0", "refin_frequency", True, self._ctrl)

    @refin_frequency_altvolt0.setter
    def refin_frequency_altvolt0(self, value):
        self._set_iio_attr("altvoltage0", "refin_frequency", True, value, self._ctrl)

    @property
    def powerdown_altvolt0(self):
        self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl)

    @powerdown_altvolt0.setter
    def powerdown_altvolt0(self, value):
        self._set_iio_attr("altvoltage0", "powerdown", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
