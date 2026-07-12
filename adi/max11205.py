# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class max11205(rx_chan_comp):

    """MAX11205 ADC"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""
    compatible_parts = ["max11205a", "max11205b"]

    def __init__(self, uri="", device_name=""):
        """Constructor for MAX11205 class."""
        super().__init__(uri=uri, device_name=device_name)

    def __post_init__(self):
        """Preserve channel traversal and the legacy private-ID lookup."""
        self._rx_channel_names = [ch._id for ch in self._ctrl.channels]

    def _add_channel_instances(self):
        """Build wrappers from the same private channel IDs as the legacy class."""
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            wrapper = self._channel_def(self._ctrl, name)
            self.channel.append(wrapper)
            setattr(self, name, wrapper)

    class _channel(attribute):

        """MAX11205 channel"""

        def __init__(self, ctrl, channel_name):
            """Initialize a MAX11205 channel wrapper."""
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """MAX11205 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """MAX11205 channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret

    _channel_def = _channel
