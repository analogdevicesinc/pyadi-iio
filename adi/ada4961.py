# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ada4961(context_manager, attribute):

    """ Low Distortion, 3.2 GHz, RF DGA """

    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ada4961")

        if not self._ctrl:
            raise Exception("ADF4159 device not found")

    @property
    def hardwaregain(self):
        """hardwaregain: Set hardware gain. Options are:
        up to 15 dB"""
        return self._get_iio_attr("voltage0", "hardwaregain", False, self._ctrl)

    @hardwaregain.setter
    def hardwaregain(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", False, value, self._ctrl)
