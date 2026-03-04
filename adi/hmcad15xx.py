# Copyright (C) 2020-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class hmcad15xx(rx, context_manager):

    """ HMCAD15XX ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for hmcad15xx class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["axi_adc_hmcad15xx"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)


    def hmcad15xx_register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def hmcad15xx_register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    @property
    def clk_div(self):
        return self._get_iio_dev_attr_str("clk_div")
    @clk_div.setter
    def clk_div(self, value):
        self._set_iio_dev_attr_str("clk_div", value, self._ctrl)

    @property
    def operation_mode(self):
     return self._get_iio_dev_attr_str("operation_mode", self._ctrl)
    @operation_mode.setter
    def operation_mode(self, value):
        self._set_iio_dev_attr_str("operation_mode", value, self._ctrl)

    class _channel(attribute):

        """ hmcad15xx channel """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def input_select(self):
            """HMCAD15XX channel input_select value"""
            return self._get_iio_attr_str(self.name, "input_select", False)

        @input_select.setter
        def input_select(self, value):
            self._set_iio_attr(self.name, "input_select", False, value)
