# Copyright (C) 2022-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4020(rx, context_manager):
    """AD4000 series of differential SAR ADC device"""

    _compatible_parts = [
        "ad4020",
        "ad4021",
        "ad4022",
    ]

    _device_name = ""
    _rx_data_type = np.int32
    _complex_data = False
    _rx_channel_names = ["voltage0"]

    def __init__(self, uri="", device_name="ad4020"):
        if not device_name:
            _device_name = self._compatible_parts[0]
        elif device_name not in self._compatible_parts:
            raise Exception(f"Not a compatible device: {device_name}")
        else:
            _device_name = device_name

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device(_device_name)
        self._ctrl = self._ctx.find_device(_device_name)

        # Dynamically get channel after the index
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            setattr(self, name, self._channel_adc(self._ctrl, name, output))

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get and set the sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set the sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", str(value))

    class _channel_adc(attribute):
        """AD4000 series differential input voltage channel"""

        # AD4000 series ADC channel
        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self._output)

        @property
        def scale(self):
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def scale_available(self):
            """Provides all available scale(gain) settings for the ADC channel"""
            return self._get_iio_attr(self.name, "scale_available", False)

        def __call__(self):
            """Convenience function, get voltages in IIO units (millivolts)"""
            return self.raw * self.scale


class ad4000(ad4020):
    _compatible_parts = [
        "ad4000",
        "ad4004",
        "ad4008",
    ]

    _rx_data_type = np.int16

    def __init__(self, uri="ip:analog.local", device_name="ad4000"):
        super().__init__(uri, device_name)


class ad4001(ad4020):
    _compatible_parts = [
        "ad4001",
        "ad4005",
    ]

    _rx_data_type = np.int16

    def __init__(self, uri="ip:analog.local", device_name="ad4001"):
        super().__init__(uri, device_name)


class ad4002(ad4020):
    _compatible_parts = [
        "ad4002",
        "ad4006",
        "ad4010",
    ]

    _rx_data_type = np.int32

    def __init__(self, uri="ip:analog.local", device_name="ad4002"):
        super().__init__(uri, device_name)


class ad4003(ad4020):
    _compatible_parts = [
        "ad4003",
        "ad4007",
        "ad4011",
    ]

    _rx_data_type = np.int32

    def __init__(self, uri="ip:analog.local", device_name="ad4003"):
        super().__init__(uri, device_name)


class adaq4003(ad4020):
    _compatible_parts = [
        "adaq4001",
        "adaq4003",
    ]

    _rx_data_type = np.int32

    def __init__(self, uri="ip:analog.local", device_name="adaq4003"):
        super().__init__(uri, device_name)
