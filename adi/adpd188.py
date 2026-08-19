# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.device_base import rx_chan_comp


class adpd188(rx_chan_comp):

    """ADPD188 photo-electronic device."""

    channel = []  # type: ignore
    _complex_data = False
    _device_name = ""
    compatible_parts = ["adpd188"]

    def __init__(self, uri="", device_index=0):
        """ADPD188 class constructor."""
        context_manager.__init__(self, uri, self._device_name)
        devices = [device for device in self._ctx.devices if device.name == "adpd188"]
        if device_index >= len(devices):
            raise Exception(
                f"No device found with name adpd188 at index {device_index}"
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
            """Initialize an ADPD188 channel wrapper."""
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

    _channel_def = _channel
