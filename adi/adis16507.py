# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


class adis16507(rx, context_manager):
    """ ADIS16507 Precision, Miniature MEMS IMU """

    _complex_data = False
    _rx_channel_names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
    ]
    _device_name = ""
    _rx_data_si_type = float

    def __init__(
        self, uri="", imu_dev_name="adis16507-3", trigger_name="adis16507-3-dev0"
    ):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(imu_dev_name)
        self._rxadc = self._ctx.find_device(imu_dev_name)
        # Set default trigger
        self._trigger = self._ctx.find_device(trigger_name)
        self._rxadc._set_trigger(self._trigger)
        rx.__init__(self)
        self.rx_buffer_size = 16  # Make default buffer smaller

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def filter_low_pass_3db_frequency(self):
        """filter_low_pass_3db_frequency: Bandwidth for the accelerometer and
        gyroscope channels"""
        return self._get_iio_dev_attr("filter_low_pass_3db_frequency")

    @filter_low_pass_3db_frequency.setter
    def filter_low_pass_3db_frequency(self, value):
        self._set_iio_dev_attr_str("filter_low_pass_3db_frequency", value)

    @property
    def current_timestamp_clock(self):
        """current_timestamp_clock: Source clock for timestamps"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    @current_timestamp_clock.setter
    def current_timestamp_clock(self, value):
        self._set_iio_dev_attr_str("current_timestamp_clock", value)
