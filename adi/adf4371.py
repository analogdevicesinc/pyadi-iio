# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4371(attribute, context_manager):
    """ADF4371 Microwave Wideband Synthesizer
    with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4371
    """

    _device_name = "adf4371"
    _muxout_options = (
        "tristate",
        "digital_lock",
        "charge_pump_up",
        "charge_pump_down",
        "RDIV2",
        "N_div_out",
        "VCO_test",
        "high",
        "VCO_calib_R_band",
        "VCO_calib_N_band",
    )

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4371 device not found")

    @property
    def muxout_mode(self):
        """Get/Set the MUX output mode"""
        return self._get_iio_dev_attr("muxout_mode", self._ctrl)

    @muxout_mode.setter
    def muxout_mode(self, value):
        """Get/Set the MUX output mode"""

        # Check that the value is valid
        if value.lower().strip() not in self._muxout_options:
            raise ValueError(
                f"muxout_mode of \"{value}\" is invalid. Valid options: {', '.join(self._muxout_options)}"
            )

        self._set_iio_dev_attr("muxout_mode", value, self._ctrl)

    @property
    def rf8_enable(self):
        """Get/Set the enable status of the 8GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl))
        )

    @rf8_enable.setter
    def rf8_enable(self, value):
        """Get/Set the enable status of the 8GHz RF output"""
        self._set_iio_attr("altvoltage0", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf8_frequency(self):
        """Get/Set the frequency of the 8GHz RF output"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @rf8_frequency.setter
    def rf8_frequency(self, value):
        """Get/Set the frequency of the 8GHz RF output"""
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def rfaux8_enable(self):
        """Get/Set the enable status of the Auxiliary 8GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage1", "powerdown", True, self._ctrl))
        )

    @rfaux8_enable.setter
    def rfaux8_enable(self, value):
        """Get/Set the enable status of the Auxiliary 8GHz RF output"""
        self._set_iio_attr("altvoltage1", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rfaux8_frequency(self):
        """Get/Set the frequency of the Auxiliary 8GHz RF output"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @rfaux8_frequency.setter
    def rfaux8_frequency(self, value):
        """Get/Set the frequency of the Auxiliary 8GHz RF output"""
        self._set_iio_attr("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def rf16_enable(self):
        """Get/Set the enable status of the 16GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage2", "powerdown", True, self._ctrl))
        )

    @rf16_enable.setter
    def rf16_enable(self, value):
        """Get/Set the enable status of the 16GHz RF output"""
        self._set_iio_attr("altvoltage2", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf16_frequency(self):
        """Get/Set the frequency of the 16GHz RF output"""
        return self._get_iio_attr("altvoltage2", "frequency", True, self._ctrl)

    @rf16_frequency.setter
    def rf16_frequency(self, value):
        """Get/Set the frequency of the 16GHz RF output"""
        self._set_iio_attr("altvoltage2", "frequency", True, value, self._ctrl)

    @property
    def rf32_enable(self):
        """Get/Set the enable status of the 32GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage3", "powerdown", True, self._ctrl))
        )

    @rf32_enable.setter
    def rf32_enable(self, value):
        """Get/Set the enable status of the 32GHz RF output"""
        self._set_iio_attr("altvoltage3", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf32_frequency(self):
        """Get/Set the frequency of the 32GHz RF output"""
        return self._get_iio_attr("altvoltage3", "frequency", True, self._ctrl)

    @rf32_frequency.setter
    def rf32_frequency(self, value):
        """Get/Set the frequency of the 32GHz RF output"""
        self._set_iio_attr("altvoltage3", "frequency", True, value, self._ctrl)

    @property
    def temperature(self):
        """Get the temperature reading"""
        return self._get_iio_attr("temp0", "input", False)
