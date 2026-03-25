# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx

# TODO: add support for events when libiio gains support for it


class ad2s1210(rx, context_manager):
    """
    AD2S1210 resolver to digital converter.
    """

    _device_name = "ad2s1210"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctrl = self._ctx.find_device(self._device_name)
        self._rx_channel_names = []

        for ch in self._ctrl.channels:
            name = ch.id

            if name == "angl0":
                self._rx_channel_names.append(name)
                self.position = self._position_channel(self._ctrl, name)
            elif name == "anglvel0":
                self._rx_channel_names.append(name)
                self.velocity = self._velocity_channel(self._ctrl, name)

        rx.__init__(self)

    @property
    def excitation_frequency(self) -> int:
        """
        Gets and sets the excitation frequency in Hz.

        Setting the value also does a soft reset of the device so that the
        physical output is updated for the change.
        """
        return self._get_iio_attr("altvoltage0", "frequency", True)

    @excitation_frequency.setter
    def excitation_frequency(self, value: int) -> None:
        self._set_iio_attr("altvoltage0", "frequency", True, value)

    @property
    def hysteresis_enable(self) -> bool:
        """
        Gets and sets the hysteresis bit in the Control register.
        """
        return bool(self._get_iio_attr("angl0", "hysteresis", False))

    @hysteresis_enable.setter
    def hysteresis_enable(self, value: bool) -> None:
        # This is just a boolean bit flag in the Control register but the
        # IIO ABI requires us to use raw angle units so we have to look up
        # the available values to find out what the raw value is for True.
        # `avail` will be a list of two int values.
        avail = self._get_iio_attr("angl0", "hysteresis_available", False)
        self._set_iio_attr("angl0", "hysteresis", False, avail[bool(value)])

    class _position_channel(attribute):
        """AD2S1210 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self) -> int:
            """AD2S1210 position channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self) -> float:
            """AD2S1210 position channel scale"""
            return float(self._get_iio_attr(self.name, "scale", False))

    class _velocity_channel(attribute):
        """AD2S1210 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self) -> int:
            """AD2S1210 velocity channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self) -> float:
            """AD2S1210 velocity channel scale"""
            return float(self._get_iio_attr(self.name, "scale", False))
