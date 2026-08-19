# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class max14001_channel(attribute):

    """MAX14001 channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX14001 channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """MAX14001 channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """MAX14001 channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @property
    def offset(self):
        """MAX14001 channel offset."""
        return self._get_iio_attr(self.name, "offset", False)


class max14001(rx_chan_comp):

    """MAX14001 ADC"""

    _complex_data = False
    _device_name = ""
    _channel_def = max14001_channel
    _rx_channel_names = ["voltage"]
    compatible_parts = [
        "max14001",
        "max14002",
    ]

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale  # offset

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return
