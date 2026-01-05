# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adxl355(rx, context_manager, attribute):
    """ ADXL355 3-axis accelerometer """

    _device_name = "adxl355"
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _rx_data_type = np.int32

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("adxl355")
        self.accel_x = self._channel(self._ctrl, "accel_x")
        self.accel_y = self._channel(self._ctrl, "accel_y")
        self.accel_z = self._channel(self._ctrl, "accel_z")
        self.temp = self._tempchannel(self._ctrl, "temp")
        self._rxadc = self._ctx.find_device("adxl355")
        self._rx_channel_names = ["accel_x", "accel_y", "accel_z"]
        rx.__init__(self)

    @property
    def current_timestamp_clock(self):
        """Current timestamp clock"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    def to_degrees(self, raw):
        """Convert raw to degrees Celsius"""
        return (raw + self.temp.offset) * self.temp.scale / 1000.0

    class _tempchannel(attribute):
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

    class _channel(attribute):
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
            return self._get_iio_attr(
                self.name, "filter_high_pass_3db_frequency", False
            )

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
