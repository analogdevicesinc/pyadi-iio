# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4377(attribute, context_manager):
    """ADF4377 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4377
    """

    _device_name = "adf4377"
    _charge_pump_options = (
        "0.790000",
        "0.990000",
        "1.190000",
        "1.380000",
        "1.590000",
        "1.980000",
        "2.390000",
        "2.790000",
        "3.180000",
        "3.970000",
        "4.770000",
        "5.570000",
        "6.330000",
        "7.910000",
        "9.510000",
        "11.100000",
    )

    _rfout_div_options = (
        "1",
        "2",
        "4",
        "8",
    )

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4377 device not found")

    @property
    def volt0_en(self):
        """Get/Set the enable/disable state of channel 0"""
        return bool(self._get_iio_attr("voltage0", "enable", True, self._ctrl))

    @volt0_en.setter
    def volt0_en(self, value):
        """Set the enable/disable state of channel 0"""
        self._set_iio_attr("voltage0", "enable", True, int(value), self._ctrl)

    @property
    def volt0_output_power(self):
        """Get/Set the output power of channel 0"""
        return self._get_iio_attr("voltage0", "output_power", True, self._ctrl)

    @volt0_output_power.setter
    def volt0_output_power(self, value):
        """Set the output power of channel 0"""
        self._set_iio_attr_int("voltage0", "output_power", True, int(value), self._ctrl)

    @property
    def volt0_frequency(self):
        """Get/Set the rfout frequency of channel 0"""
        return self._get_iio_attr("voltage0", "frequency", True, self._ctrl)

    @volt0_frequency.setter
    def volt0_frequency(self, value):
        """Set the rfout frequency of channel 0"""
        self._set_iio_attr_int("voltage0", "frequency", True, value, self._ctrl)

    @property
    def volt1_en(self):
        """Get/Set the enable/disable state of channel 1"""
        return bool(self._get_iio_attr("voltage1", "enable", True, self._ctrl))

    @volt1_en.setter
    def volt1_en(self, value):
        """Set the enable/disable state of channel 1"""
        self._set_iio_attr("voltage1", "enable", True, int(value), self._ctrl)

    @property
    def volt1_output_power(self):
        """Get/Set the output power of channel 1"""
        return self._get_iio_attr("voltage1", "output_power", True, self._ctrl)

    @volt1_output_power.setter
    def volt1_output_power(self, value):
        """Set the output power of channel 1"""
        self._set_iio_attr_int("voltage1", "output_power", True, int(value), self._ctrl)

    @property
    def volt1_frequency(self):
        """Get/Set the rfout frequency of channel 1"""
        return self._get_iio_attr("voltage1", "frequency", True, self._ctrl)

    @volt1_frequency.setter
    def volt1_frequency(self, value):
        """Set the rfout frequency of channel 1"""
        self._set_iio_attr_int("voltage1", "frequency", True, value, self._ctrl)

    @property
    def reference_frequency(self):
        """Get/Set the reference frequency"""
        return self._get_iio_dev_attr("reference_clock", self._ctrl)

    @reference_frequency.setter
    def reference_frequency(self, value):
        """Set the reference frequency"""
        self._set_iio_dev_attr("reference_clock", value, self._ctrl)

    @property
    def reference_divider(self):
        """Get/Set the reference divider"""
        return self._get_iio_dev_attr("reference_divider", self._ctrl)

    @reference_divider.setter
    def reference_divider(self, value):
        """Set the reference divider"""
        self._set_iio_dev_attr("reference_divider", value, self._ctrl)

    @property
    def reference_doubler_enable(self):
        """Get/Set the enable state of the reference doubler"""
        return self._get_iio_dev_attr("reference_doubler_enable", self._ctrl)

    @reference_doubler_enable.setter
    def reference_doubler_enable(self, value):
        """Set the enable state of the reference doubler"""
        self._set_iio_dev_attr("reference_doubler_enable", value, self._ctrl)

    @property
    def charge_pump_current(self):
        """Get/Set the charge pump current in mA"""
        return self._get_iio_dev_attr("charge_pump_current", self._ctrl)

    @charge_pump_current.setter
    def charge_pump_current(self, value):
        """Set the charge pump current in mA"""
        # Check that the value is valid
        if value.lower().strip() not in self._charge_pump_options:
            raise ValueError(
                f"charge_pump_current of \"{value}\" is invalid. Valid options: {', '.join(self._charge_pump_options)}"
            )
        self._set_iio_dev_attr("charge_pump_current", value, self._ctrl)

    @property
    def bleed_current(self):
        """Get/Set the bleed word value"""
        return self._get_iio_dev_attr("bleed_current", self._ctrl)

    @bleed_current.setter
    def bleed_current(self, value):
        """Set the bleed word value"""
        self._set_iio_dev_attr("bleed_current", value, self._ctrl)

    @property
    def rfout_divider(self):
        return self._get_iio_dev_attr("rfout_divider", self._ctrl)

    @rfout_divider.setter
    def rfout_divider(self, value):
        # Check that the divider value is valid
        if value.lower().strip() not in self._rfout_div_options:
            raise ValueError(
                f"rfout_divider of \"{value}\" is invalid. Valid options: {', '.join(self._rfout_div_options)}"
            )

        self._set_iio_dev_attr("rfout_divider", value, self._ctrl)

    @property
    def sysref_delay_adjust(self):
        """Get/Set the SYSREF delay adjustment value"""
        return self._get_iio_dev_attr("sysref_delay_adjust", self._ctrl)

    @sysref_delay_adjust.setter
    def sysref_delay_adjust(self, value):
        """Set the SYSREF delay adjustment value"""
        self._set_iio_dev_attr("sysref_delay_adjust", value, self._ctrl)

    @property
    def sysref_invert_adjust(self):
        """Get/Set the enable/disable state of SYSREF inversion"""
        return bool(self._get_iio_dev_attr("sysref_invert_adjust", self._ctrl))

    @sysref_invert_adjust.setter
    def sysref_invert_adjust(self, value):
        """Set the enable/disable state of SYSREF inversion"""
        self._set_iio_dev_attr("sysref_invert_adjust", int(value), self._ctrl)

    @property
    def sysref_monitoring(self):
        """Get/Set the enable/disable state of SYSREF monitoring"""
        return bool(self._get_iio_dev_attr("sysref_monitoring", self._ctrl))

    @sysref_monitoring.setter
    def sysref_monitoring(self, value):
        """Set the enable/disable state of SYSREF monitoring"""
        self._set_iio_dev_attr("sysref_monitoring", int(value), self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
