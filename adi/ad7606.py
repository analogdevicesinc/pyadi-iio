# Copyright (C) 2021-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7606(rx, context_manager):
    """ AD7606 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad7605-4",
            "ad7606-4",
            "ad7606-6",
            "ad7606-8",
            "ad7606b",
            "ad7606c-16",
            "ad7606c-18",
            "ad7616",
        ]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def scale_available(self):
        """Provides all available scale settings for the AD7606 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    @property
    def range_available(self):
        """Provides all available range settings for the AD7606 channels"""
        return self._get_iio_attr(self.channel[0].name, "range_available", False)

    @property
    def oversampling_ratio(self):
        """AD7606 oversampling_ratio"""
        return self._get_iio_attr(self.name, "oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._get_iio_attr(self.name, "oversampling_ratio", False, value)

    @property
    def oversampling_ratio_available(self):
        """AD7606 channel oversampling_ratio_available"""
        return self._get_iio_attr(self.name, "oversampling_ratio_available", False)

    class _channel(attribute):
        """AD7606 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7606 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7606 channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def range(self):
            """AD7606 channel range"""
            return self._get_iio_attr(self.name, "range", False)

        @range.setter
        def range(self, value):
            self._set_iio_attr(self.name, "range", False, str(Decimal(value).real))

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
