# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad7405_channel(attribute):
    """AD7405 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def scale(self):
        """Get scale of voltage input"""
        return float(self._get_iio_attr(self.name, "scale", False, self._ctrl))

    @property
    def offset(self):
        """Get offset of voltage input"""
        return int(self._get_iio_attr(self.name, "offset", False, self._ctrl))


class ad7405(rx_chan_comp):

    """ AD7405 ADC """

    compatible_parts = ["adum7701", "adum7702", "adum7703", "ad7405"]
    _complex_data = False
    _channel_def = ad7405_channel
    _device_name = "adum7701"

    @property
    def oversampling_ratio(self):
        """Get oversampling ratio"""
        return int(self._get_iio_dev_attr("oversampling_ratio", False))

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        available = self.oversampling_ratio_available
        if value not in available:
            raise ValueError(
                f"Oversampling ratio '{value}' invalid. Valid: {available}"
            )
        self._set_iio_dev_attr("oversampling_ratio", value)

    @property
    def oversampling_ratio_available(self):
        """Return list of valid oversampling ratios"""
        raw = self._get_iio_dev_attr("oversampling_ratio_available", False)
        if isinstance(raw, list):
            return raw
        return list(map(int, raw.strip().split()))
