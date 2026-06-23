# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adpd188(rx, context_manager):

    """ADPD188 photo-electronic device."""

    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_index=0):
        """ADPD188 class constructor."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["adpd188"]

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

    @property
    def mode(self):
        """Read mode of operation to device."""
        return self._get_iio_dev_attr_str("mode", self._rxadc)

    @mode.setter
    def mode(self, value):
        self._set_iio_dev_attr_str("mode", value, self._rxadc)

    @property
    def sample_rate(self):
        """Sets sampling frequency of the ADPD188."""
        return self._get_iio_attr(self.channel[0].name, "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr(self.channel[0].name, "sampling_frequency", False, value)

    class _channel(attribute):

        """ADPD188 channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADPD188 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def offset(self):
            """ADPD188 channel offset."""
            return self._get_iio_attr(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._get_iio_attr(self.name, "offset", False, value)

        @property
        def mode_available(self):
            """Read mode of operation to device."""
            return self._get_iio_attr_str(
                self.name, "mode_available", False, self._rxadc
            )
