# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
from collections import OrderedDict

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad74413r(rx, context_manager):

    _device_name = "ad74413r"
    disable_trigger = False

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ad74413r")
        self._rxadc = self._ctx.find_device("ad74413r")
        self._trigger = None
        self._rx_channel_names = []
        self._tx_channel_names = []

        self.rx_channel = []
        self.tx_channel = []

        if not self._ctrl:
            raise Exception("No ad74413r device found")

        _rx_channels = []
        _tx_channels = []
        _channels = []
        for ch in self._ctrl.channels:
            ch_obj = self._channel(self._ctrl, ch.id, ch.output)
            if ch.output:
                self._tx_channel_names.append(ch.id)
                _tx_channels.append((ch.id, ch_obj))
            else:
                self._rx_channel_names.append(ch.id)
                _rx_channels.append((ch.id, ch_obj))
            _channels.append((ch.id, ch_obj))
        self.channel = OrderedDict(_channels)
        self.rx_channel = OrderedDict(_rx_channels)
        self.tx_channel = OrderedDict(_tx_channels)

        if not self.disable_trigger:
            for trigger_name in ["ad74413r-dev0", "sw_trig"]:
                trigger = self._ctx.find_device(trigger_name)
                if not trigger:
                    continue
                try:
                    self._rxadc._set_trigger(trigger)
                    self._trigger = trigger
                    break
                except OSError:
                    continue

        rx.__init__(self)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_attr(
            self._rx_channel_names[0], "sampling_frequency", False
        )

    @sample_rate.setter
    def sample_rate(self, value):
        for channel_name in self._rx_channel_names:
            channel = self._ctrl.find_channel(channel_name, False)
            if "sampling_frequency" in channel.attrs:
                self._set_iio_attr(channel_name, "sampling_frequency", False, value)

    def rx(self):
        try:
            data = super().rx()
        except OSError as ex:
            if ex.errno not in (1, 2) or self._rx_unbuffered_data:
                raise
            self._rxbuf = None
            self._rx_unbuffered_data = True
            return super().rx()

        if self._rx_unbuffered_data:
            return data

        data_channels = data if isinstance(data, list) else [data]
        if any(np.max(np.abs(channel_data)) != 0 for channel_data in data_channels):
            return data

        if not any(
            self._get_iio_attr(self._rx_channel_names[index], "raw", False) != 0
            for index in self.rx_enabled_channels
        ):
            return data

        self._rxbuf = None
        self._rx_unbuffered_data = True
        return super().rx()

    def reg_read(self, reg):
        return self._ctrl.reg_read(reg)

    def reg_write(self, reg, value):
        return self._ctrl.reg_write(reg, value)

    class _channel(attribute):
        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self.output = output

        @property
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self.output)

        @raw.setter
        def raw(self, value):
            return self._set_iio_attr(self.name, "raw", self.output, value)

        @property
        def scale(self):
            return self._get_iio_attr(self.name, "scale", self.output)

        @property
        def offset(self):
            return self._get_iio_attr(self.name, "offset", self.output)

        @property
        def sampling_frequency(self):
            return self._get_iio_attr(self.name, "sampling_frequency", self.output)

        @sampling_frequency.setter
        def sampling_frequency(self, value):
            return self._set_iio_attr(
                self.name, "sampling_frequency", self.output, value
            )

        @property
        def sampling_frequency_available(self):
            return self._get_iio_attr(
                self.name, "sampling_frequency_available", self.output
            )

        @property
        def diag_function(self):
            return self._get_iio_attr_str(self.name, "diag_function", self.output)

        @property
        def diag_function_available(self):
            return self._get_iio_attr_str(
                self.name, "diag_function_available", self.output
            )

        @diag_function.setter
        def diag_function(self, value):
            return self._set_iio_attr(self.name, "diag_function", self.output, value)
