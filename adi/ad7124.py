# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad7124_channel(attribute):
    """AD7124 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7124 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

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

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, value)


class ad7124(rx_chan_comp):
    """AD7124 ADC"""

    compatible_parts = ["ad7124-8", "ad7124-4"]
    _device_name = ""
    _complex_data = False
    _channel_def = ad7124_channel

    def __post_init__(self):
        """Post-initialization to sort channel names."""
        # Sort channel names by numeric suffix
        if self._rx_channel_names and "-" in self._rx_channel_names[0]:
            self._rx_channel_names.sort(key=lambda x: int(x[7:].split("-")[0]))
        elif self._rx_channel_names:
            self._rx_channel_names.sort(key=lambda x: int(x[7:]))

    @property
    def sample_rate(self):
        """Sets sampling frequency of the AD7124"""
        return self._get_iio_attr(self.channel[0].name, "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        for ch in self.channel:
            self._set_iio_attr(ch.name, "sampling_frequency", False, value)

    @property
    def scale_available(self):
        """Provides all available scale(gain) settings for the AD7124 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale
        _offset = self.channel[index].offset

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale + _offset

        if isinstance(val, np.ndarray):
            ret = [x * _scale + _offset for x in val]

        return ret
