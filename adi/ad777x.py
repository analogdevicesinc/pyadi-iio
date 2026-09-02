# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad777x_channel(attribute):
    """AD777x channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD777x channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD777x channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """AD777x channel offset."""
        return float(self._get_iio_attr_str(self.name, "offset", False))

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))


class ad777x(rx_chan_comp):
    """AD777x ADC"""

    compatible_parts = ["ad7770", "ad7771", "ad7779"]
    _device_name = ""
    _complex_data = False
    _channel_def = ad777x_channel
