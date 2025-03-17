# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad9508(attribute, context_manager):

    """ AD9508 ADC """

    _device_name = ""

    def __init__(self, uri="", device_name="ad9508"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_part = "ad9508"
        self._ctrl = None

        if not device_name:
            device_name = compatible_part
        else:
            if device_name != compatible_part:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ad9508 device not found")

        self.channel = []
        for ch in self._ctrl.channels:
            name = ch.id
            self.channel.append(self._channel(self._ctrl, name))

    class _channel(attribute):
        """AD9508 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def frequency(self):
            """Get the channel output frequency"""
            return self._get_iio_attr(self.name, "frequency", True)

        @frequency.setter
        def frequency(self, frequency):
            """Set the channel output frequency"""
            self._set_iio_attr(self.name, "frequency", False, frequency, self._ctrl)

        @property
        def phase(self):
            """Get the channel output phase"""
            return self._get_iio_attr(self.name, "phase", False)

        @phase.setter
        def phase(self, phase):
            """Set the channel output phase"""
            self._set_iio_attr(self.name, "phase", False, phase, self._ctrl)

        @property
        def raw(self):
            """Get the state of a channel divider (enabled/powered-down)"""
            return self._get_iio_attr(self.name, "raw", False)

        @raw.setter
        def raw(self, raw):
            """Set the state of a channel divider (enabled/powered-down)"""
            self._set_iio_attr(self.name, "raw", False, raw, self._ctrl)

    @property
    def sync_dividers(self):
        """Get dividers synchronization status"""
        raise AttributeError("Cannot access 'sync_dividers' directly")

    @sync_dividers.setter
    def sync_dividers(self, value):
        """Set dividers synchronization procedure"""
        self._set_iio_dev_attr("sync_dividers", value)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
