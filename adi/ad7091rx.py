# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7091rx(rx, context_manager):
    """AD7091R-2/AD7091R-4/AD7091R-8 SPI interface,
       2-/4-/8-channel, 12-bit SAR ADC"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad7091r-2",
            "ad7091r-4",
            "ad7091r-8",
        ]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[2]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Selecting the device matching device_name AD7091RX family as working device.
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
            setattr(self, name, self._channel(self._ctrl, name))

        rx.__init__(self)

    class _channel(attribute):
        """AD7091R-8/-4/-2 Input Voltage Channels"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7091r channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7091r channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

    def to_mvolts(self, index, val):
        """Converts raw value to mV"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
