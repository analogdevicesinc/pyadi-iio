# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ltc2378_channel(attribute):
    """LTC2378 channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize an LTC2378 channel."""
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


class ltc2378(rx_chan_comp):

    """ LTC2378 ADC """

    _complex_data = False
    _device_name = ""
    _channel_def = ltc2378_channel
    compatible_parts = [
        "ltc2378-20",
        "ltc2338-18",
        "ltc2364-16",
        "ltc2364-18",
        "ltc2367-16",
        "ltc2367-18",
        "ltc2368-16",
        "ltc2368-18",
        "ltc2369-18",
        "ltc2370-16",
        "ltc2376-16",
        "ltc2376-18",
        "ltc2376-20",
        "ltc2377-16",
        "ltc2377-18",
        "ltc2377-20",
        "ltc2378-16",
        "ltc2378-18",
        "ltc2379-18",
        "ltc2380-16",
    ]

    @property
    def sampling_frequency(self):
        """Get sampling frequency"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling frequency"""
        self._set_iio_dev_attr("sampling_frequency", value)
