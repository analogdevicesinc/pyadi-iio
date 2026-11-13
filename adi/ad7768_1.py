# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7768_1(rx, context_manager):

    """ AD7768-1 1-channel, Dynamic Signal Analysis Sigma-Delta ADC """

    _device_name = " "
    _rx_data_type = np.int32

    def __init__(self, uri="ip:analog.local", device_name=""):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7768-1", "adaq7767-1", "adaq7768-1", "adaq7769-1"]

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

    @property
    def sampling_frequency_available(self):
        """Get available sampling frequencies."""
        return self._get_iio_dev_attr("sampling_frequency_available")

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        if rate in self.sampling_frequency_available:
            self._set_iio_dev_attr("sampling_frequency", rate)
        else:
            raise ValueError(
                "Error: Sampling frequency not supported \nUse one of: "
                + str(self.sampling_frequency_available)
            )

    @property
    def common_mode_voltage_available(self):
        """Get common mode voltage available."""
        return self._get_iio_dev_attr_str("common_mode_voltage_available")

    @property
    def common_mode_voltage(self):
        """Get common mode voltage."""
        return self._get_iio_dev_attr_str("common_mode_voltage")

    @common_mode_voltage.setter
    def common_mode_voltage(self, rate):
        """Set sampling frequency."""
        if rate in self.common_mode_voltage_available:
            self._set_iio_dev_attr_str("common_mode_voltage", rate)
        else:
            raise ValueError(
                "Error: Common mode voltage not supported \nUse one of: "
                + str(self.common_mode_voltage_available)
            )

    class _channel(attribute):
        """AD7768-1 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def value(self):
            """AD7768-1 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7768-1 channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))
