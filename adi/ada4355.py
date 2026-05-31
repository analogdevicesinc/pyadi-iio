# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ada4355_channel(attribute):

    """ ada4355 channel """

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def scale(self):
        """Get channel scale value"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        """Set channel scale value"""
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def raw(self):
        """Get channel raw value (single sample)"""
        return self._get_iio_attr(self.name, "raw", False)


class ada4355(rx_chan_comp):

    """ ADA4355 ADC """

    _complex_data = False
    _device_name = "ada4355"
    _channel_def = ada4355_channel
    compatible_parts = ["ada4355"]

    def ada4355_register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def ada4355_register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")
