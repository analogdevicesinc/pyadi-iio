# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from collections import OrderedDict

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7746(rx, context_manager):
    """ AD7746 CDC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad7745",
            "ad7746",
            "ad7747",
        ]

        self._ctrl = None

        if device_name not in compatible_parts:
            raise Exception("Not a compatible device: " + device_name)

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            print("Found device {}".format(device.name))
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break
        # dynamically get channels
        _channels = []
        self._rx_channel_names = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            if "capacitance" in ch.id:
                _channels.append((ch.id, self._cap_channel(self._ctrl, ch.id)))
                continue
            if "temp" in ch.id:
                _channels.append((ch.id, self._temp_channel(self._ctrl, ch.id)))
                continue
            if "voltage" in ch.id:
                _channels.append((ch.id, self._volt_channel(self._ctrl, ch.id)))
                continue
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

    class _temp_channel(attribute):
        """AD7746 temperature channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def input(self):
            """AD7746 channel input value."""
            return self._get_iio_attr(self.name, "input", False)

    class _volt_channel(attribute):
        """AD7746 voltage channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7746 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7746 channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @property
        def sampling_frequency(self):
            """AD7746 channel sampling frequency."""
            return self._get_iio_attr_str(self.name, "sampling_frequency", False)

        @sampling_frequency.setter
        def sampling_frequency(self, value):
            self._set_iio_attr(self.name, "sampling_frequency", False, str(value))

        @property
        def sampling_frequency_available(self):
            """AD7746 channel's available sampling frequency."""
            sfa = self._get_iio_attr_str(
                self.name, "sampling_frequency_available", False
            )
            return [int(s) for s in sfa.split(" ")]

        def calibscale_calibration(self, value=1):
            """AD7746 scale calibration."""
            self._set_iio_attr(self.name, "calibscale_calibration", False, str(value))

    class _cap_channel(_volt_channel):
        """AD7746 capacitance channel."""

        @property
        def offset(self):
            """AD7746 channel offset."""
            return self._get_iio_attr_str(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, str(value))

        @property
        def calibscale(self):
            """AD7746 channel calibscale value."""
            return self._get_iio_attr(self.name, "calibscale", False)

        @calibscale.setter
        def calibscale(self, value):
            return self._set_iio_attr_float(self.name, "calibscale", False, value)

        @property
        def calibbias(self):
            """AD7746 channel calibbias value."""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            return self._set_iio_attr(self.name, "calibbias", False, value)

        def calibbias_calibration(self, value=1):
            """AD7746 bias calibration."""
            self._set_iio_attr(self.name, "calibbias_calibration", False, str(value))
