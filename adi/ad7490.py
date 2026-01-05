# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7490(rx, context_manager):
    """AD7490 ADC"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad7490",
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
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def polarity_available(self):
        """Provides all available polarity settings for the AD7490 channels"""
        return self._get_iio_dev_attr_str("polarity_available")

    @property
    def range_available(self):
        """Provides all available range settings for the AD7490 channels"""
        return self._get_iio_dev_attr_str("range_available")

    @property
    def polarity(self):
        """AD7490 polarity"""
        return self._get_iio_dev_attr_str("polarity")

    @polarity.setter
    def polarity(self, ptype):
        """Set polarity."""
        if ptype in self.polarity_available:
            self._set_iio_dev_attr_str("polarity", ptype)
        else:
            raise ValueError(
                "Error: Polarity type not supported \nUse one of: "
                + str(self.polarity_available)
            )

    @property
    def range(self):
        """AD7490 range"""
        return self._get_iio_dev_attr_str("range")

    @range.setter
    def range(self, rtype):
        """Set range."""
        if rtype in self.range_available:
            self._set_iio_dev_attr_str("range", rtype)
        else:
            raise ValueError(
                "Error: Range type not supported \nUse one of: "
                + str(self.range_available)
            )

    @property
    def sampling_frequency(self):
        """AD7490 sampling frequency"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    class _channel(attribute):
        """AD7490 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7490 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7490 channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
