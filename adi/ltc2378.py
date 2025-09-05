# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2378(rx, context_manager):

    """ LTC2378 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = "ltc2378"

    def __init__(self, uri="", device_name="ltc2378"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ltc2378",
        ]
        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception(f"{device_name} device not found")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch.id
            self._rx_channel_names.append(name)
            self.channel.append(_channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get sampling frequency"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling frequency"""
        self._set_iio_dev_attr("sampling_frequency", value)


class _channel(attribute):
    """LTC2378 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def scale(self):
        """Get scale value"""
        return self._get_iio_attr(self.name, "scale", False)

    @scale.setter
    def scale(self, value):
        """Set scale value"""
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def sampling_frequency(self):
        """Get sampling frequency"""
        return self._get_iio_dev_attr("sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling frequency"""
        self._set_iio_dev_attr("sampling_frequency", value)
