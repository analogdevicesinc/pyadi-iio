# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import device_base


class adrf5720(attribute, device_base):
    """ ADRF5720 Digital Attenuator """

    compatible_parts = [
        "adrf5702",
        "adrf5703",
        "adrf5720",
        "adrf5730",
        "adrf5731",
    ]

    def __init__(self, uri="", device_name=""):
        device_base.__init__(self, device_name=device_name, uri=uri)

    @property
    def attenuation(self):
        """Sets attenuation of the ADRF5720"""
        return abs(self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl))

    @attenuation.setter
    def attenuation(self, value):
        self._set_iio_attr(
            "voltage0", "hardwaregain", True, -1 * abs(value), self._ctrl
        )
