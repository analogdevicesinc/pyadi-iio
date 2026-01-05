# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ltc2314_14(attribute, context_manager):
    """LTC2314-14 14-Bit, 4.5Msps Serial Sampling ADC

    parameters:
        uri: type=string
            URI of IIO context with LTC2314-14
    """

    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the main and trigger devices
        self._ctrl = self._ctx.find_device("ltc2314-14")

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("LTC2314-14 device not found")

    @property
    def lsb_mv(self):
        """ Get the LSB in millivolts """
        return self._get_iio_attr("voltage0", "scale", False, self._ctrl)

    @property
    def voltage(self):
        """ Get the voltage reading from the ADC """
        code = self._get_iio_attr("voltage0", "raw", False, self._ctrl)
        return code * self.lsb_mv / 1000
