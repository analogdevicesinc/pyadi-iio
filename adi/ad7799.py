# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7799(rx, context_manager):
    """ AD7799 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _rx_channel_names = ["channel0", "channel1", "channel2"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("AD7799")

        self.channel = []
        for name in self._rx_channel_names:
            self.channel.append(self._channel(self._rxadc, name))

    @property
    def gain(self):
        """Get gain of the AD7799"""
        return self._get_iio_dev_attr_str("gain", self._rxadc)

    @gain.setter
    def gain(self, value):
        """Sets gain of the AD7799"""
        self._set_iio_dev_attr_str("gain", value, self._rxadc)

    class _channel(attribute):
        """AD7799 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def value(self):
            """AD7124 channel mV value"""
            return self._get_iio_attr(self.name, "volts", False, self._ctrl)
