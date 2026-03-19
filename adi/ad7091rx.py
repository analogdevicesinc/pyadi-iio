# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp_no_buff


class ad7091rx_channel(attribute):
    """AD7091R-8/-4/-2 Input Voltage Channels"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7091r channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD7091r channel scale"""
        return float(self._get_iio_attr_str(self.name, "scale", False))


class ad7091rx(rx_chan_comp_no_buff):
    """AD7091R-2/AD7091R-4/AD7091R-8 SPI interface,
       2-/4-/8-channel, 12-bit SAR ADC"""

    compatible_parts = ["ad7091r-8", "ad7091r-4", "ad7091r-2"]
    _complex_data = False
    _channel_def = ad7091rx_channel
    _device_name = ""

    def to_mvolts(self, index, val):
        """Converts raw value to mV"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
