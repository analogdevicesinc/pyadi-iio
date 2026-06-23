# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adpd410x(rx, context_manager):
    """ adpd410x Multimodal Sensor Front End """

    _complex_data = False
    channel = []  # type: ignore
    _rx_channel_names = [
        "channel0",
        "channel1",
        "channel2",
        "channel3",
        "channel4",
        "channel5",
        "channel6",
        "channel7",
    ]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("adpd410x")

        self.channel = []
        for name in self._rx_channel_names:
            self.channel.append(self._channel(self._rxadc, name))

    @property
    def sampling_frequency(self):
        """Get sampling frequency of the adpd410x"""
        return self._get_iio_dev_attr_str("sampling_frequency", self._rxadc)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Sets sampling frequency of the adpd410x"""
        self._set_iio_dev_attr_str("sampling_frequency", value, self._rxadc)

    @property
    def last_timeslot(self):
        """Get last timeslot of the adpd410x"""
        return self._get_iio_dev_attr_str("last_timeslot", self._rxadc)

    @last_timeslot.setter
    def last_timeslot(self, value):
        """Sets last timeslot of the adpd410x"""
        self._set_iio_dev_attr_str("last_timeslot", value, self._rxadc)

    @property
    def operation_mode(self):
        """Get operation mode of the adpd410x"""
        return self._get_iio_dev_attr_str("operation_mode", self._rxadc)

    @operation_mode.setter
    def operation_mode(self, value):
        """Sets operation mode of the adpd410x"""
        self._set_iio_dev_attr_str("operation_mode", value, self._rxadc)

    class _channel(attribute):
        """adpd410x channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ adpd410x channel raw value"""
            return self._get_iio_attr(self.name, "raw", False, self._ctrl)
