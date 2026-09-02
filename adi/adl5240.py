# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adl5240(attribute, context_manager):
    """ ADL5240 100 MHz TO 4000 MHz RF/IF Digitally Controlled VGA """

    _device_name = "adl5240"

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception("ADL5240 device not found")

    @property
    def hardwaregain(self):
        """hardwaregain: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage0", "hardwaregain", True)

    @hardwaregain.setter
    def hardwaregain(self, value):
        self._set_iio_attr_float("voltage0", "hardwaregain", True, value, self._ctrl)
