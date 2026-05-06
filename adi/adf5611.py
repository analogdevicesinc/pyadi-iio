# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf5611(attribute, context_manager):
    """ADF5611 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF5611
    """

    _device_name = "adf5611"
    _charge_pump_options = (
        "0.200000",
        "0.400000",
        "0.600000",
        "0.800000",
        "1.000000",
        "1.200000",
        "1.400000",
        "1.600000",
        "1.800000",
        "2.000000",
        "2.200000",
        "2.400000",
        "2.600000",
        "2.800000",
        "3.000000",
        "3.200000",
    )

    _rfoutdiv_divider_options = (
        "1",
        "2",
        "4",
        "8",
        "16",
        "32",
        "64",
        "128",
    )

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF5611 device not found")

    @property
    def rfout_frequency(self):
        """Get/Set the rfout frequency in Hz"""
        return self._get_iio_attr("altvoltage0", "rfout_frequency", True, self._ctrl)

    @rfout_frequency.setter
    def rfout_frequency(self, value):
        """Get/Set the rfout frequency in Hz"""
        self._set_iio_attr(
            "altvoltage0", "rfout_frequency", True, int(value), self._ctrl
        )

    @property
    def altvolt0_rfout_power(self):
        return self._get_iio_attr("altvoltage0", "rfout_power", True, self._ctrl)

    @altvolt0_rfout_power.setter
    def altvolt0_rfout_power(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "rfout_power", True, int(value), self._ctrl
        )

    @property
    def reference_frequency(self):
        return self._get_iio_dev_attr("reference_frequency", self._ctrl)

    @reference_frequency.setter
    def reference_frequency(self, value):
        self._set_iio_dev_attr("reference_frequency", value, self._ctrl)

    @property
    def reference_divider(self):
        return self._get_iio_dev_attr("reference_divider", self._ctrl)

    @reference_divider.setter
    def reference_divider(self, value):
        self._set_iio_dev_attr("reference_divider", value, self._ctrl)

    @property
    def charge_pump_current(self):
        return self._get_iio_dev_attr("charge_pump_current", self._ctrl)

    @charge_pump_current.setter
    def charge_pump_current(self, value):
        # Check that the value is valid
        if value.lower().strip() not in self._charge_pump_options:
            raise ValueError(
                f"charge_pump_current of \"{value}\" is invalid. Valid options: {', '.join(self._charge_pump_options)}"
            )

        self._set_iio_dev_attr("charge_pump_current", value, self._ctrl)

    @property
    def rfoutdiv_power(self):
        return self._get_iio_dev_attr("rfoutdiv_power", self._ctrl)

    @rfoutdiv_power.setter
    def rfoutdiv_power(self, value):
        self._set_iio_dev_attr("rfoutdiv_power", value, self._ctrl)

    @property
    def rfoutdiv_divider(self):
        return self._get_iio_dev_attr("rfoutdiv_divider", self._ctrl)

    @rfoutdiv_divider.setter
    def rfoutdiv_divider(self, value):
        # Check that the divider value is valid
        if value.lower().strip() not in self._rfoutdiv_divider_options:
            raise ValueError(
                f"rfoutdiv_divider of \"{value}\" is invalid. Valid options: {', '.join(self._rfoutdiv_divider_options)}"
            )

        self._set_iio_dev_attr("rfoutdiv_divider", value, self._ctrl)

    @property
    def en_rfoutdiv(self):
        return self._get_iio_dev_attr("en_rfoutdiv", self._ctrl)

    @en_rfoutdiv.setter
    def en_rfoutdiv(self, value):
        self._set_iio_dev_attr("en_rfoutdiv", value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
