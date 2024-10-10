# Copyright (C) 2019-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np
from adi.context_manager import context_manager
from adi.rx_tx import rx
from adi.attribute import attribute

class ad9094(rx, context_manager):
    """ AD9094 Quad ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl  = self._ctx.find_device("axi-ad9094-hpc")
        self._rxadc = self._ctx.find_device("axi-ad9094-hpc")

        self.channel = []

        for name in self._rx_channel_names:
            self.channel.append(self._channel(self._rxadc, name))

        rx.__init__(self)

    def register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._rxadc)
        return self._get_iio_debug_attr_str("direct_reg_access", self._rxadc)

    def register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._rxadc)

    class _channel(attribute):

        """AD9094 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def test_mode(self):
            """AD9094 channel test mode value"""
            return self._get_iio_attr_str(self.name, "test_mode", False, self._ctrl)
        @test_mode.setter
        def test_mode(self, value):
            self._set_iio_attr(self.name, "test_mode", False, value, self._ctrl)
