# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.compatible import compatible


class adrf5720(attribute, compatible):
    """ ADRF5720 Digital Attenuator """

    _channel = "voltage0"

    compatible_parts = [
        "adrf5702",
        "adrf5703",
        "adrf5720",
        "adrf5730",
        "adrf5731",
    ]

    def __init__(self, uri="", device_name=""):
        compatible.__init__(self, uri, device_name)

    @property
    def attenuation(self):
        """Sets attenuation of the ADRF5720"""
        return abs(
            self._get_iio_attr(adrf5720._channel, "hardwaregain", True, self._ctrl)
        )

    @attenuation.setter
    def attenuation(self, value):
        self._set_iio_attr(
            adrf5720._channel, "hardwaregain", True, -1 * abs(value), self._ctrl
        )
