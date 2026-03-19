# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad7689_channel(attribute):
    """AD7689 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7689 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD7689 channel scale"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))


class ad7689(rx_chan_comp):
    """AD7689 ADC"""

    channel = []  # type: ignore
    compatible_parts = [
        "ad7689",
        "ad7682",
        "ad7949",
        "ad7699",
        "ad7690",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad7689_channel

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
