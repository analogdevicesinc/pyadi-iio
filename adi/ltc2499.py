# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
from collections import OrderedDict

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2499(rx, context_manager):

    channel: OrderedDict = None
    _device_name = "ltc2499"
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ltc2499")

        if not self._ctrl:
            raise Exception("No device found")

        _channels = []
        self._rx_channel_names = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            _channels.append((ch.id, self._channel(self._ctrl, ch.id)))
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

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

        @property
        def value(self):
            return self.raw * self.scale
