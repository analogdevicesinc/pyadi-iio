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
        #self._ctx = iio.Context("ip:10.75.161.150")
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4355 device not found")

    @property
    def altvolt0_bleed_pol(self):
        """Get/Set the bleed polarity state of channel 0:
        0: current sink.
        1: current source."""
        return bool(self._get_iio_attr("altvoltage0", "bleed_pol", True, self._ctrl))

    @altvolt0_bleed_pol.setter
    def altvolt0_bleed_pol(self, value):
        """Get/Set the bleed polarity state of channel 0:
        0: current sink.
        1: current source."""
        self._set_iio_attr("altvoltage0", "bleed_pol", True, int(value), self._ctrl)

    @property
    def altvolt0_en(self):
        """Get/Set the enable/disable state of channel 0"""
        return bool(self._get_iio_attr("altvoltage0", "en", True, self._ctrl))

    @altvolt0_en.setter
    def altvolt0_en(self, value):
        """Set the enable/disable state of channel 0"""
        self._set_iio_attr("altvoltage0", "en", True, int(value), self._ctrl)

    @property
    def altvolt0_en_auto_align(self):
        """Get/Set the enable/disable auto alignment state of channel 0"""
        return bool(self._get_iio_attr("altvoltage0", "en_auto_align", True, self._ctrl))

    @altvolt0_en_auto_align.setter
    def altvolt0_en_auto_align(self, value):
        """Set the enable/disable auto alignment state of channel 0"""
        self._set_iio_attr("altvoltage0", "en_auto_align", True, int(value), self._ctrl)

    @property
    def altvolt0_frequency(self):
        """Get/Set the rfout frequency of channel 0"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @altvolt0_frequency.setter
    def altvolt0_frequency(self, value):
        """Set the rfout frequency of channel 0"""
        self._set_iio_attr_int("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def altvolt0_hardwaregain(self):
        """Get/Set the hardware gain of channel 0"""
        return self._get_iio_attr("altvoltage0", "hardwaregain", True, self._ctrl)

    @altvolt0_hardwaregain.setter
    def altvolt0_hardwaregain(self, value):
        """Set the hardware gain of channel 0"""
        self._set_iio_attr_int("altvoltage0", "hardwaregain", True, value, self._ctrl)

    @property
    def altvolt0_phase(self):
        """Get/Set the phase adjustment of channel 0"""
        return self._get_iio_attr("altvoltage0", "phase", True, self._ctrl)

    @altvolt0_phase.setter
    def altvolt0_phase(self, value):
        """Set the phase adjustment of channel 0"""
        self._set_iio_attr_int("altvoltage0", "phase", True, value, self._ctrl)

    @property
    def altvolt0_coarse_current(self):
        """Get/Set the coarse_current of channel 0"""
        return self._get_iio_attr("altvoltage0", "coarse_current", True, self._ctrl)

    @altvolt0_coarse_current.setter
    def altvolt0_coarse_current(self, value):
        """Set the coarse_current of channel 0"""
        self._set_iio_attr_int("altvoltage0", "coarse_current", True, value, self._ctrl)

    @property
    def altvolt0_fine_current(self):
        """Get/Set the fine_current of channel 0"""
        return self._get_iio_attr("altvoltage0", "fine_current", True, self._ctrl)

    @altvolt0_fine_current.setter
    def altvolt0_fine_current(self, value):
        """Set the fine_current of channel 0"""
        self._set_iio_attr_int("altvoltage0", "fine_current", True, value, self._ctrl)

    @property
    def altvolt1_bleed_pol(self):
        """Get/Set the bleed polarity state of channel 1:
        0: current sink.
        1: current source."""
        return bool(self._get_iio_attr("altvoltage1", "bleed_pol", True, self._ctrl))

    @altvolt1_bleed_pol.setter
    def altvolt1_bleed_pol(self, value):
        """Get/Set the bleed polarity state of channel 1:
        0: current sink.
        1: current source."""
        self._set_iio_attr("altvoltage1", "bleed_pol", True, int(value), self._ctrl)

    @property
    def altvolt1_en(self):
        """Get/Set the enable/disable state of channel 1"""
        return bool(self._get_iio_attr("altvoltage1", "en", True, self._ctrl))

    @altvolt1_en.setter
    def altvolt1_en(self, value):
        """Set the enable/disable state of channel 1"""
        self._set_iio_attr("altvoltage1", "en", True, int(value), self._ctrl)

    @property
    def altvolt1_en_auto_align(self):
        """Get/Set the enable/disable auto alignment state of channel 1"""
        return bool(self._get_iio_attr("altvoltage1", "en_auto_align", True, self._ctrl))

    @altvolt1_en_auto_align.setter
    def altvolt1_en_auto_align(self, value):
        """Set the enable/disable auto alignment state of channel 1"""
        self._set_iio_attr("altvoltage1", "en_auto_align", True, int(value), self._ctrl)

    @property
    def altvolt1_frequency(self):
        """Get/Set the rfout frequency of channel 1"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @altvolt1_frequency.setter
    def altvolt1_frequency(self, value):
        """Set the rfout frequency of channel 1"""
        self._set_iio_attr_int("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def altvolt1_hardwaregain(self):
        """Get/Set the hardware gain of channel 1"""
        return self._get_iio_attr("altvoltage1", "hardwaregain", True, self._ctrl)

    @altvolt1_hardwaregain.setter
    def altvolt1_hardwaregain(self, value):
        """Set the hardware gain of channel 1"""
        self._set_iio_attr_int("altvoltage1", "hardwaregain", True, value, self._ctrl)

    @property
    def altvolt1_phase(self):
        """Get/Set the phase adjustment of channel 1"""
        return self._get_iio_attr("altvoltage1", "phase", True, self._ctrl)

    @altvolt1_phase.setter
    def altvolt1_phase(self, value):
        """Set the phase adjustment of channel 1"""
        self._set_iio_attr_int("altvoltage1", "phase", True, value, self._ctrl)

    @property
    def altvolt1_coarse_current(self):
        """Get/Set the coarse_current of channel 1"""
        return self._get_iio_attr("altvoltage1", "coarse_current", True, self._ctrl)

    @altvolt1_coarse_current.setter
    def altvolt1_coarse_current(self, value):
        """Set the coarse_current of channel 1"""
        self._set_iio_attr_int("altvoltage1", "coarse_current", True, value, self._ctrl)

    @property
    def altvolt1_fine_current(self):
        """Get/Set the fine_current of channel 1"""
        return self._get_iio_attr("altvoltage1", "fine_current", True, self._ctrl)

    @altvolt1_fine_current.setter
    def altvolt1_fine_current(self, value):
        """Set the fine_current of channel 1"""
        self._set_iio_attr_int("altvoltage1", "fine_current", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
