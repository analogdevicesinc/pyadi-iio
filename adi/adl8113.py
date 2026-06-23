# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adl8113(attribute, context_manager):
    """ADL8113 GPIO-controlled RF Amplifier"""

    _device_name = "adl8113"

    def __init__(self, uri="", device_name="adl8113"):
        context_manager.__init__(self, uri, self._device_name)
        compatible_part = "adl8113"
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
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADL8113 device not found")

    @property
    def hardwaregain(self):
        """Get hardware gain in dB"""
        return self._get_iio_attr("voltage", "hardwaregain", False, self._ctrl)

    @hardwaregain.setter
    def hardwaregain(self, value):
        """Set hardware gain in dB"""
        self._set_iio_attr("voltage", "hardwaregain", False, value, self._ctrl)
