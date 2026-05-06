# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class adxl355_tempchannel(attribute):
    """ADXL355 temperature channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def offset(self):
        """ADXL355 temperature offset value"""
        return self._get_iio_attr(self.name, "offset", False)

    @property
    def raw(self):
        """ADXL355 temperature raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """ADXL355 channel scale value"""
        return self._get_iio_attr(self.name, "scale", False)


class adxl355_channel(attribute):
    """ADXL355 acceleration channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def calibbias(self):
        """ADXL355 channel offset"""
        return self._get_iio_attr(self.name, "calibbias", False)

    @calibbias.setter
    def calibbias(self, value):
        self._set_iio_attr(self.name, "calibbias", False, value)

    @property
    def filter_high_pass_3db_frequency(self):
        """ADXL355 highpass filter cutoff frequency"""
        return self._get_iio_attr(self.name, "filter_high_pass_3db_frequency", False)

    @filter_high_pass_3db_frequency.setter
    def filter_high_pass_3db_frequency(self, value):
        self._set_iio_attr(
            self.name,
            "filter_high_pass_3db_frequency",
            False,
            str(Decimal(value).real),
        )

    @property
    def filter_high_pass_3db_frequency_available(self):
        """Provides all available highpass filter cutoff frequency settings for the ADXL355 channels"""
        return self._get_iio_attr(
            self.name, "filter_high_pass_3db_frequency_available", False
        )

    @property
    def raw(self):
        """ADXL355 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """ADXL355 channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @property
    def sampling_frequency_available(self):
        """Provides all available sampling frequency settings for the ADXL355 channels"""
        return self._get_iio_attr(self.name, "sampling_frequency_available", False)

    @property
    def sampling_frequency(self):
        """ADXL355 per-channel sampling frequency"""
        return float(self._get_iio_attr_str(self.name, "sampling_frequency", False))

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr(
            self.name, "sampling_frequency", False, str(Decimal(value).real)
        )


class adxl355(rx_chan_comp):
    """ ADXL355 3-axis accelerometer """

    compatible_parts = ["adxl355"]
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _rx_data_type = np.int32
    _complex_data = False
    _channel_def = adxl355_channel
    _control_device_name = "adxl355"
    _rx_data_device_name = "adxl355"
    _rx_channel_names = ["accel_x", "accel_y", "accel_z"]

    __run_rx_post_init__ = False

    def __init__(self, uri="", **kwargs):
        rx_chan_comp.__init__(self, uri, **kwargs)
        self._setup_channels()

    def _setup_channels(self):
        """Set up named channel access and temperature channel."""
        # Add named channel access for accelerometer channels
        self.accel_x = self.channel[0] if len(self.channel) > 0 else None
        self.accel_y = self.channel[1] if len(self.channel) > 1 else None
        self.accel_z = self.channel[2] if len(self.channel) > 2 else None

        # Add temperature channel separately since it's not in _rx_channel_names
        self.temp = adxl355_tempchannel(self._ctrl, "temp")

    @property
    def current_timestamp_clock(self):
        """Current timestamp clock"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    def to_degrees(self, raw):
        """Convert raw to degrees Celsius"""
        return (raw + self.temp.offset) * self.temp.scale / 1000.0
