# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class _ad7124_channel(attribute):
    """AD7124 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7124 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def filter_type_available(self):
        """Provide all available filter types for the selected channel."""
        return self._get_iio_attr_str(self.name, "filter_type_available", False)

    @property
    def filter_type(self):
        """Get the AD7124 channel filter type."""
        return self._get_iio_attr_str(self.name, "filter_type", False)

    @filter_type.setter
    def filter_type(self, ftype):
        """Set filter type."""
        if ftype in self.filter_type_available:
            self._set_iio_attr(self.name, "filter_type", False, ftype)
        else:
            raise ValueError(
                "Error: Filter type not supported \nUse one of: "
                + str(self.filter_type_available)
            )

    @property
    def scale_available(self):
        """Provide all available scale settings for the selected channel."""
        return self._get_iio_attr(self.name, "scale_available", False)

    @property
    def scale(self):
        """AD7124 channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """AD7124 channel offset"""
        return self._get_iio_attr(self.name, "offset", False)

    # @offset.setter
    # def offset(self, value):
    #     self._set_iio_attr(self.name, "offset", False, value)

    @property
    def sampling_frequency(self):
        """Get the sampling frequency of the selected channel."""
        return self._get_iio_attr(self.name, "sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr(self.name, "sampling_frequency", False, value)

    @property
    def sys_calibration_mode_available(self):
        """Return the available system calibration modes."""
        return self._get_iio_attr_str(
            self.name, "sys_calibration_mode_available", False
        )

    @property
    def sys_calibration_mode(self):
        """Return the system calibration mode."""
        return self._get_iio_attr_str(self.name, "sys_calibration_mode", False)

    @sys_calibration_mode.setter
    def sys_calibration_mode(self, calmode):
        """Set filter type."""
        if calmode in self.sys_calibration_mode_available:
            self._set_iio_attr(self.name, "sys_calibration_mode", False, calmode)
        else:
            raise ValueError(
                "Error: This calibration mode not supported \nUse one of: "
                + str(self.sys_calibration_mode_available)
            )

    @property
    def sys_calibration(self):
        """Return the system calibration state."""
        raise AttributeError(
            "sys_calibration is write only; write 1 to calibrate.\
                              This is a self-clear bit"
        )

    @sys_calibration.setter
    def sys_calibration(self, cal):
        # accept any argument, 1 is the only valid value.
        self._set_iio_attr(self.name, "sys_calibration", False, 1)

    def __call__(self, mV=None):
        """Get the channel reading in millivolts."""
        return (self.raw + self.offset) * self.scale


class _temp_channel(_ad7124_channel):
    @property
    def scale_available(self):
        raise AttributeError("scale_available not applicable to temp channel")

    @property
    def scale(self):
        """Get the AD7124 temperature scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        raise AttributeError("scale not applicable to temp channel")

    def __call__(self, mV=None):
        """Get the temperature in degrees Celsius."""
        return ((self.raw + self.offset) * self.scale) / 1000


class ad7124(rx_chan_comp):  # noqa: D203,D211,D212,D213
    """AD7124 4/8-channel, low-noise, low-power, 24-bit sigma-delta ADC.

    Analog input configuration (single-ended, differential, unipolar, bipolar) is set in
    the device tree. This class scans all channels and creates both a ``channel[]`` list
    attribute and individual channel attributes for channel IDs that are valid Python
    identifiers, for example:

    - ``my_ad7124.temp`` (temperature sensor)
    - ``my_ad7124.voltage0`` (single-ended voltage input)

    Differential channels such as ``voltage0-voltage1`` are available through
    ``channel[]`` and with ``getattr(my_ad7124, "voltage0-voltage1")``.

    The ``enable_single_cycle`` device attribute defaults to 'Y', and ensures that when
    a single channel is enabled, output data is fully settled; intermediate, unsettled
    outputs from the digital filter are ignored. Setting to 'N' includes these unsettled
    samples, increasing the output data rate accordingly.

    Each voltage channel has the following sub-attributes:

    - ``raw`` -- Raw ADC code (read only)
    - ``scale`` / ``scale_available`` -- ADC scale (millivolts per LSB) and available scales
    - ``filter_type`` / ``filter_type_available`` -- Digital filter type
    - ``sampling_frequency`` -- Per-channel sampling frequency
    - ``__call__()`` -- Returns reading in millivolts

    The temperature channel is the same, with these exceptions:

    - ``scale`` does not have a setter
    - ``scale_available`` does not apply (raises error)
    - ``__call__()`` returns temperature in degrees Celsius
    """

    def __repr__(self):
        """Return a representation containing the URI and device documentation."""
        retstr = f"""
ad7124(uri="{self.uri}, device_name={self._device_name})"

{self.__doc__}
"""
        return retstr

    compatible_parts = ["ad7124-8", "ad7124-4"]
    _device_name = ""
    _complex_data = False
    _channel_def = {"temp": _temp_channel, "voltage": _ad7124_channel}

    @property
    def enable_single_cycle(self):
        """Get single-cycle mode for settled, no-latency conversions."""
        return self._get_iio_debug_attr_str("enable_single_cycle", self._ctrl)

    @enable_single_cycle.setter
    def enable_single_cycle(self, value):
        self._set_iio_debug_attr_str("enable_single_cycle", value, self._ctrl)
