# Copyright (C) 2019-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class adis16475(rx, context_manager):
    """ADIS16475 Compact, Precision, Six Degrees of Freedom Inertial Sensor"""

    _complex_data = False
    _rx_channel_names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
        "temp0",
    ]
    _device_name = ""

    def __init__(self, uri="", device_name="adis16505-2"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "adis16470",
            "adis16475-1",
            "adis16475-2",
            "adis16475-3",
            "adis16477-1",
            "adis16477-2",
            "adis16477-3",
            "adis16465-1",
            "adis16465-2",
            "adis16465-3",
            "adis16467-1",
            "adis16467-2",
            "adis16467-3",
            "adis16500",
            "adis16505-1",
            "adis16505-2",
            "adis16505-3",
            "adis16507-1",
            "adis16507-2",
            "adis16507-3",
        ]

        if device_name not in compatible_parts:
            raise Exception(
                "Not a compatible device:"
                + str(device_name)
                + ".Please select from:"
                + str(compatible_parts)
            )
        else:
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)

        rx.__init__(self)
        self.rx_buffer_size = 16  # Make default buffer smaller

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)
