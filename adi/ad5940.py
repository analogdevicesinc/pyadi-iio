# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import struct
from collections import OrderedDict

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad5940(rx, context_manager):
    """ ad5940 CDC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri=""):

        device_name = "ad5940"
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break
        # dynamically get channels
        _channels = []
        self._rx_channel_names = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            if ch.name == "bia":
                _channels.append((ch.id, self._bia_channel(self, self._ctrl, ch.id)))
                continue
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

    @property
    def impedance_mode(self):
        """In impedance mode, device measures voltage and current and to
        compute the impedance. Otherwise, only the voltage is measured."""
        return bool(int(self._get_iio_dev_attr("impedance_mode", self._rxadc)))

    @impedance_mode.setter
    def impedance_mode(self, value):
        self._set_iio_dev_attr("impedance_mode", int(value), self._rxadc)

    @property
    def magnitude_mode(self):
        """In magnitude mode, device computes and returns the magnitude.
        Otherwise, a pair of real and imaginary parts of the complex
        result is returned by the device."""
        return bool(int(self._get_iio_dev_attr("magnitude_mode", self._rxadc)))

    @magnitude_mode.setter
    def magnitude_mode(self, value):
        self._set_iio_dev_attr("magnitude_mode", int(value), self._rxadc)

    @property
    def excitation_frequency(self):
        """Excitation frequency."""
        return self._get_iio_dev_attr("excitation_frequency", self._rxadc)

    @excitation_frequency.setter
    def excitation_frequency(self, value):
        self._set_iio_dev_attr("excitation_frequency", value, self._rxadc)

    @property
    def excitation_amplitude(self):
        """Excitation amplitude."""
        return self._get_iio_dev_attr("excitation_amplitude", self._rxadc)

    @excitation_amplitude.setter
    def excitation_amplitude(self, value):
        self._set_iio_dev_attr("excitation_amplitude", value, self._rxadc)

    @property
    def gpio1_toggle(self):
        """GPIO1 control."""
        return bool(int(self._get_iio_dev_attr("gpio1_toggle", self._rxadc)))

    @gpio1_toggle.setter
    def gpio1_toggle(self, value):
        self._set_iio_dev_attr("gpio1_toggle", int(value), self._rxadc)

    class _bia_channel(attribute):
        """ad5940 bio-impedance analysis channel."""

        def __init__(self, parent, ctrl, channel_name):
            self.name = channel_name
            self._parent = parent
            self._ctrl = ctrl

        @property
        def raw(self):
            """ad5940 channel raw value."""
            raw = self._get_iio_attr(self.name, "raw", False)
            impedance_mode = self._parent.impedance_mode
            magnitude_mode = self._parent.magnitude_mode
            if impedance_mode:
                if magnitude_mode:
                    return struct.unpack(
                        ">f", int(raw).to_bytes(4, byteorder="big", signed=True)
                    )[0]
                else:
                    return complex(
                        struct.unpack(
                            ">f", int(raw[0]).to_bytes(4, byteorder="big", signed=True)
                        )[0],
                        struct.unpack(
                            ">f", int(raw[1]).to_bytes(4, byteorder="big", signed=True)
                        )[0],
                    )
            else:
                if magnitude_mode:
                    return struct.unpack(
                        ">f", int(raw).to_bytes(4, byteorder="big", signed=True)
                    )[0]
                else:
                    return complex(int(raw[0]), int(raw[1]))
