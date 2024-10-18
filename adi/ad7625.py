# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7625(rx, context_manager):
    """AD7625 device"""

    _compatible_parts = [
        "ad7625",
        "ad7626",
        "ad7960",
        "ad7961",
    ]

    _device_name = ""
    _complex_data = False
    _rx_channel_names = ["voltage0-voltage1"]

    def __init__(self, uri="", device_name="ad7625"):
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
