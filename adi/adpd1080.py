# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.device_base import rx_chan_comp


class adpd1080(rx_chan_comp):
    """ADPD1080 photo-electronic device."""

    channel = []  # type: ignore
    _complex_data = False
    _device_name = ""
    compatible_parts = ["adpd1080"]

    def __init__(self, uri="", device_index=0):
        """ADPD1080 class constructor."""
        context_manager.__init__(self, uri, self._device_name)
        devices = [device for device in self._ctx.devices if device.name == "adpd1080"]
        if device_index >= len(devices):
            raise Exception(
                f"No device found with name adpd1080 at index {device_index}"
            )
        self._rx_channel_names = [ch._id for ch in devices[device_index]._channels]
        super().__init__(uri=self._ctx, device_index=device_index)

    def __post_init__(self):
        """Use the legacy smaller default RX buffer."""
        self.rx_buffer_size = 16

    def _add_channel_instances(self):
        """Build wrappers from private IIO channel traversal order."""
        self.channel = []
        for ch in self._ctrl._channels:
            name = ch._id
            wrapper = self._channel_def(self._ctrl, name)
            self.channel.append(wrapper)
            setattr(self, name, wrapper)

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
            """Initialize an ADPD1080 channel wrapper."""
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

    _channel_def = _channel
