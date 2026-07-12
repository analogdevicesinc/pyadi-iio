# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
from collections import OrderedDict

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ltc2499(rx_chan_comp):

    channel: OrderedDict = None
    _complex_data = False
    _device_name = "ltc2499"
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    compatible_parts = ["ltc2499"]

    def __init__(self, uri=""):
        """Initialize the LTC2499 while preserving its URI-only API."""
        super().__init__(uri=uri)

    def __post_init__(self):
        """Preserve all-channel traversal rather than scan-only discovery."""
        self._rx_channel_names = [ch.id for ch in self._ctrl.channels]

    def _add_channel_instances(self):
        """Preserve the public OrderedDict channel container."""
        self.channel = OrderedDict(
            (ch.id, self._channel_def(self._ctrl, ch.id)) for ch in self._ctrl.channels
        )

    class _channel(attribute):
        def __init__(self, ctrl, channel_name):
            """Initialize an LTC2499 channel wrapper."""
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

    _channel_def = _channel
