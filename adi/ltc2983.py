import numbers
from collections import OrderedDict
from collections.abc import Iterable

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2983(rx, context_manager):
    """ LTC2983 Multi-Sensor Temperature Measurement System """

    channel: OrderedDict = None
    _device_name = "ltc2983"
    _rx_unbuffered_data = True
    _rx_data_type = np.int32
    _rx_data_si_type = np.float

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ltc2983")
        self._rxadc = self._ctx.find_device("ltc2983")

        # dynamically get channels
        _channels = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            _channels.append((ch.id, self._channel(self._ctrl, ch.id)))
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

    class _channel(attribute):
        """ LTC2983 channel """

        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def raw(self):
            """Channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """Channel scale factor"""
            return np.float(self._get_iio_attr_str(self.name, "scale", False))

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
