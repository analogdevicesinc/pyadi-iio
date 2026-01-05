# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7405(rx, context_manager):

    """ AD7405 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = "adum7701"

    def __init__(self, uri="", device_name="adum7701"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "adum7701",
            "adum7702",
            "adum7703",
            "ad7405",
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
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    class _channel(attribute):
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
