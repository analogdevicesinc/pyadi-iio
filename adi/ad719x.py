# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad719x_channel(attribute):
    """AD719x channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD719X channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD719X channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """AD719x channel offset."""
        return float(self._get_iio_attr_str(self.name, "offset", False))

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))


class ad719x(rx_chan_comp):
    """AD719x ADC"""

    channel = []  # type: ignore
    compatible_parts = ["ad7190", "ad7191", "ad7192", "ad7193", "ad7194", "ad7195"]
    _device_name = ""
    _complex_data = False
    _channel_def = ad719x_channel

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale
        _offset = self.channel[index].offset

        ret = None

        if isinstance(val, np.int32):
            ret = (val + _offset) / 1000 * _scale

        if isinstance(val, np.ndarray):
            ret = [((x + _offset) / 1000) * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
