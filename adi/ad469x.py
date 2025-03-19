# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad469x(rx, context_manager):
    """ AD469x, 16-Bit, 16-Channel, Easy Drive Multiplexed SAR ADCs with sample
    rates of 500 kSPS or 1 MSPS"""

    _compatible_parts = ["ad4695", "ad4696", "ad4697", "ad4698"]
    _device_name = ""
    channel = []

    def __init__(self, uri="ip:analog.local", device_name="ad4696"):
        """Constructor for AD469x class."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        if not device_name:
            device_name = self._compatible_parts[0]
        else:
            if device_name not in self._compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        self._rxadc = self._ctrl = self._ctx.find_device(device_name)

        if not self._rxadc:
            raise Exception(f"Error in selecting matching device: {device_name}")

        if not self._ctrl:
            raise Exception(f"Error in selecting matching device: {device_name}")

        self._rx_channel_names = []
        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    class _channel(attribute):

        """AD469x channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def sampling_frequency(self):
            """Get sampling frequency of the channel."""
            return self._get_iio_attr(self.name, "sampling_frequency", False)

        @sampling_frequency.setter
        def sampling_frequency(self, rate):
            """Set sampling frequency of the channel."""
            self._set_iio_attr(
                self.name, "sampling_frequency", value=rate, output=False
            )

        @property
        def sampling_frequency_available(self):
            """Get available sampling frequency values. This property only exists if
            SPI offload is enabled for the driver."""
            return self._get_iio_attr(self.name, "sampling_frequency_available", False)

        @property
        def raw(self):
            """AD469x channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD4698 channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def offset(self):
            """AD469x channel offset."""
            return self._get_iio_attr_str(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
