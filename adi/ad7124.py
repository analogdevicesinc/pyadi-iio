# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7124(rx, context_manager):
    """ AD7124 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7124-8", "ad7124-4"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the 7124 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    break
                else:
                    index += 1

        self._rx_channel_names = [chan.id for chan in self._ctrl.channels]
        if "-" in self._rx_channel_names[0]:
            self._rx_channel_names.sort(key=lambda x: int(x[7:].split("-")[0]))
        else:
            self._rx_channel_names.sort(key=lambda x: int(x[7:]))

        for name in self._rx_channel_names:
            self.channel.append(self._channel(self._ctrl, name))
        rx.__init__(self)

    @property
    def sample_rate(self):
        """Sets sampling frequency of the AD7124"""
        return self._get_iio_attr(self.channel[0].name, "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        for ch in self.channel:
            self._set_iio_attr(ch.name, "sampling_frequency", False, value)

    @property
    def scale_available(self):
        """Provides all available scale(gain) settings for the AD7124 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    class _channel(attribute):
        """AD7124 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7124 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7124 channel scale(gain)"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def offset(self):
            """AD7124 channel offset"""
            return self._get_iio_attr(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._get_iio_attr(self.name, "offset", False, value)

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale
        _offset = self.channel[index].offset

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale + _offset

        if isinstance(val, np.ndarray):
            ret = [x * _scale + _offset for x in val]

        return ret
