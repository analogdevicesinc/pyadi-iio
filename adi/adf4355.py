# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4355(attribute, context_manager):
    """ADF4355 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4355
    """

    _device_name = "adf4355"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4355 device not found")

    @property
    def frequency_altvolt0(self):
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency_altvolt0.setter
    def frequency_altvolt0(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def powerdown_altvolt0(self):
        return bool(
            1 - int(self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl))
        )

    @powerdown_altvolt0.setter
    def powerdown_altvolt0(self, value):
        self._set_iio_attr("altvoltage0", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def frequency_altvolt1(self):
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @frequency_altvolt1.setter
    def frequency_altvolt1(self, value):
        self._set_iio_attr("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def powerdown_altvolt1(self):
        return bool(
            1 - int(self._get_iio_attr("altvoltage1", "powerdown", True, self._ctrl))
        )

    @powerdown_altvolt1.setter
    def powerdown_altvolt1(self, value):
        self._set_iio_attr("altvoltage1", "powerdown", True, 1 - int(value), self._ctrl)
