# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad469x_channel(attribute):
    """AD469x channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD469x channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD4698 channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """AD469x channel offset."""
        return self._get_iio_attr_str(self.name, "offset", False)

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))


class ad469x(rx_chan_comp):
    """AD469x ADC"""

    channel = []  # type: ignore
    compatible_parts = [
        "ad4696",
        "ad4697",
        "ad4698",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad469x_channel

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
