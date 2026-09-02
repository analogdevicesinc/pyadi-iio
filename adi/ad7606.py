# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad7606_channel(attribute):
    """AD7606 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7606 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD7606 channel scale"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def range(self):
        """AD7606 channel range"""
        return self._get_iio_attr(self.name, "range", False)

    @range.setter
    def range(self, value):
        self._set_iio_attr(self.name, "range", False, str(Decimal(value).real))


class ad7606(rx_chan_comp):
    """AD7606 ADC"""

    channel = []  # type: ignore
    compatible_parts = [
        "ad7605-4",
        "ad7606-4",
        "ad7606-6",
        "ad7606-8",
        "ad7606b",
        "ad7606c-16",
        "ad7606c-18",
        "ad7616",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad7606_channel

    @property
    def scale_available(self):
        """Provides all available scale settings for the AD7606 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    @property
    def range_available(self):
        """Provides all available range settings for the AD7606 channels"""
        return self._get_iio_attr(self.channel[0].name, "range_available", False)

    @property
    def oversampling_ratio(self):
        """AD7606 oversampling_ratio"""
        return self._get_iio_attr(self.name, "oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._get_iio_attr(self.name, "oversampling_ratio", False, value)

    @property
    def oversampling_ratio_available(self):
        """AD7606 channel oversampling_ratio_available"""
        return self._get_iio_attr(self.name, "oversampling_ratio_available", False)

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
