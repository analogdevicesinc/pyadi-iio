# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class _channel(attribute):
    def __init__(self, ctrl, channel_name):
        self._ctrl = ctrl
        self.name = channel_name

    @property
    def raw(self):
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        return float(self._get_iio_attr_str(self.name, "scale", False))


class ltc2992(rx, context_manager, attribute):
    # _device_name = "ltc2992"
    _rx_unbuffered_data = False
    _rx_data_type = np.int32
    _rx_data_si_type = float
    _rx_channel_names = ["power0", "power1"]

    def __init__(self, uri="", device_name="ltc2992_0"):
        context_manager.__init__(self, uri, device_name)
        self._ctrl = self._ctx.find_device(device_name)
        self.power_0 = _channel(self._ctrl, "power0")
        self.power_1 = _channel(self._ctrl, "power1")
        self._rxadc = self._ctx.find_device(device_name)
        # self._rx_channel_names = ["power0", "power1"]
        self._device_name = device_name
        rx.__init__(self)
