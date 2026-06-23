# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class genmux(attribute, context_manager):
    """GEN-MUX Generic IIO Mux device
    Control MUX devices via IIO device attributes

    parameters:
        uri: type=string
            URI of IIO context with GEN-MUX
    """

    _device_name = "gen-mux"

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._device_name = device_name
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("GEN-MUX device not found")

    @property
    def select_available(self):
        """Get available MUX options"""
        return self._get_iio_dev_attr_str("mux_select_available", self._ctrl)

    @property
    def select(self):
        """Get/Set the MUX select"""
        return self._get_iio_dev_attr_str("mux_select", self._ctrl)

    @select.setter
    def select(self, value):
        """Get/Set the MUX select"""
        self._set_iio_dev_attr_str("mux_select", value, self._ctrl)
