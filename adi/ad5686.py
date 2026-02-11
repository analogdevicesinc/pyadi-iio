# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.device_base import tx_chan_comp_no_buff


class ad5686_channel(attribute):
    """AD5686 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD5686 channel raw value"""
        return self._get_iio_attr(self.name, "raw", True, self._ctrl)

    @raw.setter
    def raw(self, value):
        self._set_iio_attr(self.name, "raw", True, str(int(value)))

    @property
    def powerdown(self):
        """AD5686 channel powerdown value"""
        return self._get_iio_attr(self.name, "powerdown", True)

    @powerdown.setter
    def powerdown(self, val):
        """AD5686 channel powerdown value"""
        self._set_iio_attr(self.name, "powerdown", True, val)

    @property
    def powerdown_mode(self):
        """AD5686 channel powerdown mode value"""
        return self._get_iio_attr_str(self.name, "powerdown_mode", True)

    @powerdown_mode.setter
    def powerdown_mode(self, val):
        """AD5686 channel powerdown value"""
        self._set_iio_attr_str(self.name, "powerdown_mode", True, val)

    @property
    def powerdown_mode_available(self):
        """Provides all available powerdown mode settings for the AD5686"""
        return self._get_iio_attr_str(self.name, "powerdown_mode_available", True)

    @property
    def scale(self):
        """AD5686 channel scale(gain)"""
        return self._get_iio_attr(self.name, "scale", True)

    def to_raw(self, val):
        """Converts raw value to SI"""
        return int(1000.0 * val / self.scale)

    @property
    def volts(self):
        """AD5686 channel value in volts"""
        return self.raw * self.scale

    @volts.setter
    def volts(self, val):
        """AD5686 channel value in volts"""
        self.raw = self.to_raw(val)


class ad5686(tx_chan_comp_no_buff):
    """ AD5686 DAC """

    compatible_parts = [
        "ad5686",
        "ad5310r",
        "ad5311r",
        "ad5671r",
        "ad5672r",
        "ad5673r",
        "ad5674r",
        "ad5675r",
        "ad5676",
        "ad5676r",
        "ad5677r",
        "ad5679r",
        "ad5681r",
        "ad5682r",
        "ad5683",
        "ad5683r",
        "ad5684",
        "ad5684r",
        "ad5685r",
        "ad5686r",
        "ad5691r",
        "ad5692r",
        "ad5693",
        "ad5693r",
        "ad5694",
        "ad5694r",
        "ad5695r",
        "ad5696",
        "ad5696r",
    ]
    _complex_data = False
    _channel_def = ad5686_channel
    _device_name = ""
