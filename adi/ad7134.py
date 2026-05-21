# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7134(rx, context_manager):

    """AD7134 ADC"""

    _complex_data = False
    _rx_data_type = np.int32
    channel = []  # type: ignore
    _device_name = "ad4134"

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4134", "ad7134", "adc_0", "adc_1"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        # If exact match failed, try all compatible names
        if not self._ctrl:
            for part in compatible_parts:
                for device in self._ctx.devices:
                    if device.name == part:
                        self._ctrl = device
                        self._rxadc = device
                        break
                if self._ctrl:
                    break

        if not self._ctrl:
            raise Exception(
                f"No device found with name '{device_name}'. "
                f"Compatible names: {compatible_parts}. "
                f"Available devices: {[d.name for d in self._ctx.devices]}"
            )

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """AD7134 sampling frequency in Hz"""
        return self._get_iio_attr(
            self._rx_channel_names[0], "sampling_frequency", False
        )

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        self._set_iio_attr(
            self._rx_channel_names[0], "sampling_frequency", False, str(int(rate))
        )

    @property
    def filter_type_available(self):
        """AD7134 available filter types"""
        return self._get_iio_dev_attr_str("filter_type_available")

    @property
    def filter_type(self):
        """AD7134 digital filter type"""
        return self._get_iio_dev_attr_str("filter_type")

    @filter_type.setter
    def filter_type(self, ftype):
        self._set_iio_dev_attr_str("filter_type", ftype)

    def sync(self):
        """Reset AD7134 digital interface (broadcast DIG_IF_RESET via cs_gpio)"""
        self._set_iio_dev_attr_str("ad4134_sync", "enable")

    def reg_read(self, reg):
        """Direct register access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct register access via debugfs"""
        self._set_iio_debug_attr_str(
            "direct_reg_access", f"{reg} {value}", self._ctrl
        )

    @property
    def odr_set_freq(self):
        """AD7134 ODR frequency (alias for device-level sampling_frequency)"""
        return self._get_iio_dev_attr("sampling_frequency")

    @odr_set_freq.setter
    def odr_set_freq(self, freq):
        self._set_iio_dev_attr_str("sampling_frequency", str(int(freq)))

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.int32):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret

    class _channel(attribute):

        """AD7134 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7134 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7134 channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def offset(self):
            """AD7134 channel offset"""
            return float(self._get_iio_attr_str(self.name, "offset", False))

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))
