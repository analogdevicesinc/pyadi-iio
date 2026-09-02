# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4382(attribute, context_manager):
    """ADF4382 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4382
    """

    _device_name = "adf4382"
    _charge_pump_options = (
        "0.700000",
        "0.900000",
        "1.100000",
        "1.300000",
        "1.500000",
        "1.900000",
        "2.300000",
        "2.700000",
        "3.100000",
        "3.900000",
        "4.700000",
        "5.500000",
        "6.300000",
        "7.900000",
        "9.500000",
        "11.100000",
    )

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4355 device not found")

    @property
    def altvolt0_en(self):
        """Get/Set the enable/disable state of channel 0"""
        return bool(self._get_iio_attr("altvoltage0", "en", True, self._ctrl))

    @altvolt0_en.setter
    def altvolt0_en(self, value):
        """Set the enable/disable state of channel 0"""
        self._set_iio_attr("altvoltage0", "en", True, int(value), self._ctrl)

    @property
    def altvolt0_output_power(self):
        """Get/Set the output power of channel 0"""
        return self._get_iio_attr("altvoltage0", "output_power", True, self._ctrl)

    @altvolt0_output_power.setter
    def altvolt0_output_power(self, value):
        """Set the output power of channel 0"""
        self._set_iio_attr_int(
            "altvoltage0", "output_power", True, int(value), self._ctrl
        )

    @property
    def altvolt0_frequency(self):
        """Get/Set the rfout frequency of channel 0"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @altvolt0_frequency.setter
    def altvolt0_frequency(self, value):
        """Set the rfout frequency of channel 0"""
        self._set_iio_attr_int("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def altvolt0_phase(self):
        """Get/Set the phase adjustment of channel 0"""
        return self._get_iio_attr("altvoltage0", "phase", True, self._ctrl)

    @altvolt0_phase.setter
    def altvolt0_phase(self, value):
        """Set the phase adjustment of channel 0"""
        self._set_iio_attr_int("altvoltage0", "phase", True, value, self._ctrl)

    @property
    def altvolt1_en(self):
        """Get/Set the enable/disable state of channel 1"""
        return bool(self._get_iio_attr("altvoltage1", "en", True, self._ctrl))

    @altvolt1_en.setter
    def altvolt1_en(self, value):
        """Set the enable/disable state of channel 1"""
        self._set_iio_attr("altvoltage1", "en", True, int(value), self._ctrl)

    @property
    def altvolt1_output_power(self):
        """Get/Set the output power of channel 1"""
        return self._get_iio_attr("altvoltage1", "output_power", True, self._ctrl)

    @altvolt1_output_power.setter
    def altvolt1_output_power(self, value):
        """Set the output power of channel 1"""
        self._set_iio_attr_int(
            "altvoltage1", "output_power", True, int(value), self._ctrl
        )

    @property
    def altvolt1_frequency(self):
        """Get/Set the rfout frequency of channel 1"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @altvolt1_frequency.setter
    def altvolt1_frequency(self, value):
        """Set the rfout frequency of channel 1"""
        self._set_iio_attr_int("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def altvolt1_phase(self):
        """Get/Set the phase adjustment of channel 1"""
        return self._get_iio_attr("altvoltage1", "phase", True, self._ctrl)

    @altvolt1_phase.setter
    def altvolt1_phase(self, value):
        """Set the phase adjustmet of channel 1"""
        self._set_iio_attr_int("altvoltage1", "phase", True, value, self._ctrl)

    @property
    def bleed_current(self):
        """Get/Set the bleed word value"""
        return self._get_iio_dev_attr("bleed_current", self._ctrl)

    @bleed_current.setter
    def bleed_current(self, value):
        """Set the bleed word value"""
        self._set_iio_dev_attr("bleed_current", value, self._ctrl)

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
    def reference_divider(self):
        """Get/Set the reference divider"""
        return self._get_iio_dev_attr("reference_divider", self._ctrl)

    @reference_divider.setter
    def reference_divider(self, value):
        """Set the reference divider"""
        self._set_iio_dev_attr("reference_divider", value, self._ctrl)

    @property
    def reference_doubler_en(self):
        """Get/Set the enable state of the reference doubler"""
        return self._get_iio_dev_attr("reference_doubler_en", self._ctrl)

    @reference_doubler_en.setter
    def reference_doubler_en(self, value):
        """Set the enable state of the reference doubler"""
        self._set_iio_dev_attr("reference_doubler_en", value, self._ctrl)

    @property
    def reference_frequency(self):
        """Get/Set the reference frequency"""
        return self._get_iio_dev_attr("reference_frequency", self._ctrl)

    @reference_frequency.setter
    def reference_frequency(self, value):
        """Set the reference frequency"""
        self._set_iio_dev_attr("reference_frequency", value, self._ctrl)

    @property
    def sw_sync_en(self):
        """Get/Set the enable state of software synchronization"""
        return self._get_iio_dev_attr("sw_sync_en", self._ctrl)

    @sw_sync_en.setter
    def sw_sync_en(self, value):
        """Set the enable state of software synchronization"""
        self._set_iio_dev_attr("sw_sync_en", value, self._ctrl)

    @property
    def ezsync_setup(self):
        """Get/Set the EZSync setup"""
        return self._get_iio_dev_attr("ezsync_setup", self._ctrl)

    @ezsync_setup.setter
    def ezsync_setup(self, value):
        """Set the EZSync setup"""
        self._set_iio_dev_attr("ezsync_setup", value, self._ctrl)

    @property
    def timed_sync_setup(self):
        """Get/Set the timed synchronization setup"""
        return self._get_iio_dev_attr("timed_sync_setup", self._ctrl)

    @timed_sync_setup.setter
    def timed_sync_setup(self, value):
        """Set the timed synchronization setup"""
        self._set_iio_dev_attr("timed_sync_setup", value, self._ctrl)

    @property
    def fastcal_en(self):
        """Get/Set the enable state of fast calibration"""
        return self._get_iio_dev_attr("fastcal_en", self._ctrl)

    @fastcal_en.setter
    def fastcal_en(self, value):
        """Set the enable state of fast calibration"""
        self._set_iio_dev_attr("fastcal_en", value, self._ctrl)

    @property
    def fastcal_lut_en(self):
        """Get/Set the enable state of fast calibration Lookup Table usage"""
        return self._get_iio_dev_attr("fastcal_lut_en", self._ctrl)

    @fastcal_lut_en.setter
    def fastcal_lut_en(self, value):
        """Set the enable state of fast calibration Lookup Table usage"""
        self._set_iio_dev_attr("fastcal_lut_en", value, self._ctrl)

    @property
    def change_frequency(self):
        """Get/Set the change frequency without starting calibration"""
        return self._get_iio_dev_attr("change_frequency", self._ctrl)

    @change_frequency.setter
    def change_frequency(self, value):
        """Set the change frequency without starting calibration"""
        self._set_iio_dev_attr("change_frequency", value, self._ctrl)

    @property
    def start_calibration(self):
        """Get/Set the start calibration"""
        return self._get_iio_dev_attr("start_calibration", self._ctrl)

    @start_calibration.setter
    def start_calibration(self, value):
        """Set the start calibration"""
        self._set_iio_dev_attr("start_calibration", value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
