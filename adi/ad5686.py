# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad5686(context_manager, attribute):
    """ AD5686 DAC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_index=0):
        context_manager.__init__(self, uri, self._device_name)
        # Dictionary with all compatible parts. The key of each entry is the device's id and it's value
        # is the number of bits the device supports.
        compatible_parts = [
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
            "ad5686",
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

        self._ctrl = None
        index = 0
        # We are selecting the device_index-th device from the 5686 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

        self.channel = []
        for ch in self._ctrl.channels:
            name = ch.id
            self.channel.append(self._channel(self._ctrl, name))

        # sort device channels after the index of their index
        self.channel.sort(key=lambda x: int(x.name[7:]))

    class _channel(attribute):
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
