# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.device_base import rx_def


class adis16460(rx_def):
    """ ADIS16460 Compact, Precision, Six Degrees of Freedom Inertial Sensor """

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
    _control_device_name = "adis16460"
    _rx_data_device_name = "adis16460"
    compatible_parts = ["adis16460"]

    def __init__(self, uri=""):
        """Initialize the ADIS16460 while preserving its URI-only API."""
        super().__init__(uri=uri)

    def __post_init__(self):
        """Use the legacy smaller default RX buffer."""
        self.rx_buffer_size = 16

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def current_timestamp_clock(self):
        """current_timestamp_clock: Source clock for timestamps"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    @current_timestamp_clock.setter
    def current_timestamp_clock(self, value):
        self._set_iio_dev_attr_str("current_timestamp_clock", value)
