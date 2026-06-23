# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adrf5720(attribute, context_manager):
    """ ADRF5720 Digital Attenuator """

    _complex_data = False
    channel = "voltage0"
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "adrf5720",
            "adrf5730",
            "adrf5731",
        ]

        self._ctrl = None

        for device in self._ctx.devices:
            if device.name in [device_name] + compatible_parts:
                self._ctrl = device
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADRF5720 device not found")

    @property
    def attenuation(self):
        """Sets attenuation of the ADRF5720"""
        return abs(self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl))

    @attenuation.setter
    def attenuation(self, value):
        self._set_iio_attr(
            "voltage0", "hardwaregain", True, -1 * abs(value), self._ctrl
        )
