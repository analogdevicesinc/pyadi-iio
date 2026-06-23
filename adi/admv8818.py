# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class admv8818(attribute, context_manager):
    """ADMV8818 2 GHz to 18 GHz, Digitally Tunable, High-Pass and Low-Pass Filter

    parameters:
        uri: type=string
            URI of IIO context with ADMV8818
    """

    _device_name = "admv8818"

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._device_name = device_name
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADMV8818 device not found")

    @property
    def low_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_low_pass_3db_frequency", True, self._ctrl
        )

    @low_pass_3db_frequency.setter
    def low_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0", "filter_low_pass_3db_frequency", True, int(value), self._ctrl
        )

    @property
    def high_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_high_pass_3db_frequency", True, self._ctrl
        )

    @high_pass_3db_frequency.setter
    def high_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_high_pass_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_bandwidth_3db_frequency(self):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_bandwidth_3db_frequency", True, self._ctrl
        )

    @band_pass_bandwidth_3db_frequency.setter
    def band_pass_bandwidth_3db_frequency(self, value):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_bandwidth_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_center_frequency(self):
        """Get/Set the Band Pass Center Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_center_frequency", True, self._ctrl
        )

    @band_pass_center_frequency.setter
    def band_pass_center_frequency(self, value):
        """Get/Set the Band Pass Center Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_center_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def mode_available(self):
        """Get available modes"""
        return self._get_iio_attr_str("altvoltage0", "mode_available", True, self._ctrl)

    @property
    def mode(self):
        """Get/Set mode"""
        return self._get_iio_attr_str("altvoltage0", "mode", True, self._ctrl)

    @mode.setter
    def mode(self, value):
        """Get/Set mode"""
        self._set_iio_attr("altvoltage0", "mode", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
