# Copyright (C) 2021-2024 Analog Devices, Inc.
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

        self._device_name = device_name

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
            if (name == "timestamp"):
                continue
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self, name))

        rx.__init__(self)

    @property
    def has_device_scale_available(self):
        """Returns true if the 'scale_available' attribute is at device level.
           For AD7606C-16 and AD7606C-18 in SW mode, this is available
           at channel level.
        """
        if self._device_name not in ["ad7606c-16", "ad7606c-18"]:
            return False
        try:
            _ = self._get_iio_dev_attr("scale_available")
            return True
        except Exception:
            return False

    @property
    def scale_available(self):
        """Provides all available scale settings for the AD7606 channels"""
        return self._get_iio_dev_attr("scale_available")

    @property
    def oversampling_ratio(self):
        """AD7606 oversampling_ratio"""
        return self._get_iio_dev_attr("oversampling_ratio")

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._set_iio_dev_attr("oversampling_ratio", value)

    @property
    def oversampling_ratio_available(self):
        """AD7606 channel oversampling_ratio_available"""
        return self._get_iio_dev_attr("oversampling_ratio_available")

    class _channel(attribute):
        """AD7606 channel"""

        def __init__(self, dev, channel_name):
            self.name = channel_name
            self._dev = dev
            self._ctrl = dev._ctrl

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
        def scale_available(self):
            """'scale_available' is available per channel on AD7606C-16 and AD7606C-18 in SW mode"""
            # We can't detect SW mode, so we use a try block
            try:
                return self._get_iio_attr_str(self.name, "scale_available", False)
            except Exception:
                return self._dev.scale_available

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        if isinstance(val, int):
            return val * _scale

        if isinstance(val, list):
            return [x * _scale for x in val]

        # ADC7606C-18 will return int32 samples from the driver
        if isinstance(val, np.int32):
            return val * _scale

        if isinstance(val, np.int16):
            return val * _scale

        if isinstance(val, np.ndarray):
            return [x * _scale for x in val]
