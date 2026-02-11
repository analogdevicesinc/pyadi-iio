# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class adxl345_channel(attribute):
    """ADXL345 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def calibbias(self):
        """ADXL345 channel offset"""
        return self._get_iio_attr(self.name, "calibbias", False)

    @calibbias.setter
    def calibbias(self, value):
        self._set_iio_attr(self.name, "calibbias", False, value)

    @property
    def raw(self):
        """ADXL345 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """ADXL345 channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))


class adxl345(rx_chan_comp):
    """ ADXL345 3-axis accelerometer """

    compatible_parts = ["adxl345"]
    _rx_data_type = np.int32
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _complex_data = False
    _channel_def = adxl345_channel
    _control_device_name = "adxl345"
    _rx_data_device_name = "adxl345"
    _rx_channel_names = ["accel_x", "accel_y", "accel_z"]

    __run_rx_post_init__ = False

    def __init__(self, uri="", **kwargs):
        rx_chan_comp.__init__(self, uri, **kwargs)
        self._setup_channels()

    def _setup_channels(self):
        """Set up named channel access."""
        # Add named channel access
        self.accel_x = self.channel[0] if len(self.channel) > 0 else None
        self.accel_y = self.channel[1] if len(self.channel) > 1 else None
        self.accel_z = self.channel[2] if len(self.channel) > 2 else None

    @property
    def sampling_frequency_available(self):
        """Provides all available sampling frequency settings for the ADXL345 channels"""
        return self._get_iio_dev_attr("sampling_frequency_available")

    @property
    def sampling_frequency(self):
        """ADXL345 sampling frequency"""
        # Only need to consider one channel, all others follow
        return float(self._get_iio_attr_str("accel_x", "sampling_frequency", False))

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr(
            "accel_x", "sampling_frequency", False, str(Decimal(value).real)
        )
