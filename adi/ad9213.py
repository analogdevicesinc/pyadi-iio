# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad9213(rx, context_manager):

    """AD9213 High-Speed ADC"""

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""

    def __init__(self, uri="", device_name="ad9213"):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device(device_name)
        self._ctrl = self._rxadc

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """sampling_frequency: Sample rate of the ADC in Hz"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._rxadc)

    def ad9213_register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def ad9213_register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
