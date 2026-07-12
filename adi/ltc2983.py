# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import numbers
from collections import OrderedDict
from collections.abc import Iterable

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ltc2983(rx_chan_comp):
    """ LTC2983 Multi-Sensor Temperature Measurement System """

    channel: OrderedDict = None
    _complex_data = False
    _device_name = "ltc2983"
    _rx_unbuffered_data = True
    _rx_data_type = np.int32
    _rx_data_si_type = float
    compatible_parts = ["ltc2983"]

    def __init__(self, uri=""):
        """Initialize the LTC2983 while preserving its URI-only API."""
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
        """ LTC2983 channel """

        def __init__(self, ctrl, channel_name):
            """Initialize an LTC2983 channel wrapper."""
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def raw(self):
            """Channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """Channel scale factor"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @property
        def value(self):
            """Value in real units"""
            return self.raw * self.scale

    def convert(self, channel_name, val):
        """Convert raw value(s) to real units"""
        if isinstance(channel_name, numbers.Integral):
            # self.channel is ordered
            channel_name = list(self.channel.keys())[channel_name]

        if isinstance(val, Iterable):
            # don't copy unless really needed
            try:
                val = np.asarray(val, np.int32)
            except TypeError:
                val = np.fromiter(val, np.int32)

        return val * self.channel[channel_name].scale

    _channel_def = _channel
