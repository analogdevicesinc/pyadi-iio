# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adpd1080(rx, context_manager):
    """ADPD1080 photo-electronic device."""

    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_index=0):
        """ADPD1080 class constructor."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["adpd1080"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the adpd188 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    break
                else:
                    index += 1

        # dynamically get channels and sorting them after the color
        # self._ctrl.channels.sort(key=lambda x: str(x.id[14:]))
        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl._channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
        rx.__init__(self)
        self.rx_buffer_size = 16

    def rx(self):
        buff = super().rx()
        del self._rx__rxbuf
        return buff

    @property
    def sample_rate(self):
        """Sets sampling frequency of the ADPD1080."""
        return self._get_iio_dev_attr_str("sampling_frequency", self._rxadc)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value, self._rxadc)

    class _channel(attribute):
        """ADPD1080 channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADPD1080 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def offset(self):
            """ADPD1080 channel offset."""
            return self._get_iio_attr(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, value)
