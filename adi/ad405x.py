# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import List

import numpy as np
from adi.common import rx_buffered_channel
from adi.context_manager import context_manager
from adi.rx_tx import rx

# def to_volts(self, index, val):
#     """Converts raw value to SI"""
#     _scale = self.channel[index].scale

#     ret = None

#     if isinstance(val, np.uint16):
#         ret = val * _scale

#     if isinstance(val, np.ndarray):
#         ret = [x * _scale for x in val]

#     return ret


class ad405x(rx, context_manager):
    """ AD405x ADC """

    _complex_data = False
    channels: List[rx_buffered_channel] = []  # type: ignore
    """Component channels for individual ADC access"""
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4052", "ad4050"]

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

        self.channels = []
        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channels.append(rx_buffered_channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def operating_mode_avail(self):
        """Get available operating modes."""
        return self._get_iio_dev_attr_str("operating_mode_available")

    @property
    def operating_mode(self):
        """Get operating mode."""
        return self._get_iio_dev_attr_str("operating_mode")

    @operating_mode.setter
    def operating_mode(self, value):
        """Set operating mode."""
        if value in self.operating_mode_avail:
            self._set_iio_dev_attr_str("operating_mode", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.operating_mode_avail)
            )

    @property
    def burst_sample_rate(self):
        """Get burst sample rate. Only available in Burst Averaging Mode."""
        if "burst_sample_rate" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("burst_sample_rate")
        else:
            raise ValueError(
                "Error: Burst sample rate not supported in " + self.operating_mode
            )

    @burst_sample_rate.setter
    def burst_sample_rate(self, value):
        """Set burst sample rate."""
        if "burst_sample_rate" in self._ctrl._attrs.keys():
            self._set_iio_dev_attr("burst_sample_rate", value)
        else:
            raise Exception(
                "Error: Burst sample rate not supported in " + self.operating_mode
            )

    @property
    def avg_filter_length_avail(self):
        """Get available average filter length. Only available in Burst Averaging Mode."""
        if "avg_filter_length_available" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("avg_filter_length_available")
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @property
    def avg_filter_length(self):
        """Get average filter length. Only available in Burst Averaging Mode."""
        if "avg_filter_length" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("avg_filter_length")
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @avg_filter_length.setter
    def avg_filter_length(self, value):
        """Set average filter length."""
        if "avg_filter_length_available" in self._ctrl._attrs.keys():
            if value in self.avg_filter_length_avail:
                self._set_iio_dev_attr("avg_filter_length", value)
            else:
                raise ValueError(
                    "Error: Average filter length not supported \nUse one of: "
                    + str(self.avg_filter_length_avail)
                )
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling_frequency."""
        self._set_iio_dev_attr("sampling_frequency", value)
