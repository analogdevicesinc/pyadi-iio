# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad738x_channel(attribute):
    """AD738x channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD738x channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD738x channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """AD738x channel offset."""
        return float(self._get_iio_attr_str(self.name, "offset", False))

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))


class ad738x(rx_chan_comp):
    """AD738x ADC"""

    compatible_parts = [
        "ad7381",
        "ad7380",
        "ad7380-4",
        "ad7389-4",
        "ad7381-4",
        "ad7383",
        "ad7384",
        "ad7386",
        "ad7387",
        "ad7388",
        "ad4680",
        "ad4681",
        "ad4682",
        "ad4683",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad738x_channel
    _ignore_channels = ["timestamp"]

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int32):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
