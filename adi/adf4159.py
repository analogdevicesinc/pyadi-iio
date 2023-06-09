# Copyright (C) 2021-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4159(context_manager, attribute):

    """ ADF4159 is a 13 GHz Fractional-N Frequency Synthesizer """

    _device_name = "adf4159"

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)
        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4159 device not found")

    @property
    def ramp_mode(self):
        """Get/Set the Ramp output mode."""
        return self._get_iio_attr_str("altvoltage0", "ramp_mode", True, self._ctrl)

    @ramp_mode.setter
    def ramp_mode(self, value):
        """Get/Set the Ramp output mode."""

        valid = self._get_iio_attr_str(
            "altvoltage0", "ramp_mode_available", True, self._ctrl
        )
        if value not in valid:

            raise ValueError(
                f'ramp_mode of "{value}" is invalid. Valid options: "{valid}"'
            )

        self._set_iio_attr("altvoltage0", "ramp_mode", True, value, self._ctrl)

    @property
    def enable(self):
        """Get/Set the enable status of the RF output."""
        return bool(
            int(self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl))
        )

    @enable.setter
    def enable(self, value):
        """Get/Set the enable status of the RF output."""
        self._set_iio_attr("altvoltage0", "powerdown", True, int(value), self._ctrl)

    @property
    def frequency(self):
        """Get/Set the Output Frequency of PLL."""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency.setter
    def frequency(self, value):
        """Get/Set the Output Frequency of PLL."""
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def freq_dev_range(self):
        """Get/Set the PLL frequency deviation range."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_range", True, self._ctrl
        )

    @freq_dev_range.setter
    def freq_dev_range(self, value):
        """Get/Set the PLL frequency deviation range."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_range", True, value, self._ctrl
        )

    @property
    def freq_dev_step(self):
        """Get/Set the PLL frequency deviation step."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_step", True, self._ctrl
        )

    @freq_dev_step.setter
    def freq_dev_step(self, value):
        """Get/Set the PLL frequency deviation step."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_step", True, (1 + value), self._ctrl
        )

    @property
    def freq_dev_time(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_time", True, self._ctrl
        )

    @freq_dev_time.setter
    def freq_dev_time(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_time", True, value, self._ctrl
        )
