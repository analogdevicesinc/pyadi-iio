from collections import OrderedDict
from collections.abc import Iterable
import numbers

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2983(rx, context_manager):
    """ LTC2983 Multi-Sensor Temperature Measurement System """

    _complex_data = False
    channel = None
    _device_name = ""
    _rx_data_type = np.int32

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ltc2983")
        self._rxadc = self._ctx.find_device("ltc2983")

        # dynamically get channels
        _channels = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            _channels.append((ch.id, self._channel(self._ctrl, ch)))
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

    class _channel(attribute):
        """ LTC2983 channel """

        def __init__(self, ctrl, channel):
            self._ctrl = ctrl
            self._channel = channel

            self.name = channel.id

            # raw value attribute is '<x>_raw' with
            # <x>=thermistor,rtd,diode,thermocouple,direct_adc
            raw_attr_name = [x for x in channel.attrs.keys()
                              if x.endswith("raw")]
            assert len(raw_attr_name) == 1
            raw_attr_name = raw_attr_name[0]

            self._raw_attr = self._channel.attrs[raw_attr_name]
            self._scale_attr = self._channel.attrs["scale"]

        @property
        def raw(self):
            """Channel raw value"""
            return np.int32(self._raw_attr.value)

        @property
        def scale(self):
            """Channel scale factor"""
            return np.float32(self._scale_attr.value)

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
