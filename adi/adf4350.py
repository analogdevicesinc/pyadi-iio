# Copyright (C) 2025 Analog Devices, Inc.
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
    def frequency(self):
        """Set/Get Output Frequency"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency.setter
    def frequency(self, value):
        """Set/Get Output Frequency"""
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def frequency_resolution(self):
        """Set/Get Frequency Resolution"""
        return self._get_iio_attr(
            "altvoltage0", "frequency_resolution", True, self._ctrl
        )

    @frequency_resolution.setter
    def frequency_resolution(self, value):
        """Set/Get Frequency Resolution"""
        self._set_iio_attr(
            "altvoltage0", "frequency_resolution", True, value, self._ctrl
        )

    @property
    def refin_frequency(self):
        """Set/Get Reference Frequency"""
        return self._get_iio_attr("altvoltage0", "refin_frequency", True, self._ctrl)

    @refin_frequency.setter
    def refin_frequency(self, value):
        """Set/Get Reference Frequency"""
        self._set_iio_attr("altvoltage0", "refin_frequency", True, value, self._ctrl)

    @property
    def powerdown(self):
        """Enable/Disable Powerdown PLL and RFOUT Buffers"""
        self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl)

    @powerdown.setter
    def powerdown(self, value):
        """Enable/Disable Powerdown PLL and RFOUT Buffers"""
        self._set_iio_attr("altvoltage0", "powerdown", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
