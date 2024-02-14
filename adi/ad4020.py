# Copyright (C) 2022-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4020(rx, context_manager):
    """AD4020 device"""

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
        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get and set the sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set the sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", str(value))


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
