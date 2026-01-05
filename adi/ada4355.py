# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ada4355(rx, context_manager):

    """ ADA4355 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = "ada4355"

    def __init__(self, uri="", device_name="ada4355"):
        """Constructor for ada4355 class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ada4355"]

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

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    def ada4355_register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def ada4355_register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    class _channel(attribute):

        """ ada4355 channel """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            """Get channel scale value"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            """Set channel scale value"""
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def raw(self):
            """Get channel raw value (single sample)"""
            return self._get_iio_attr(self.name, "raw", False)
