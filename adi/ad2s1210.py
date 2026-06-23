# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.rx_tx import rx_def

# TODO: add support for events when libiio gains support for it


class ad2s1210_position_channel(attribute):
    """AD2S1210 position channel"""

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


class ad2s1210_velocity_channel(attribute):
    """AD2S1210 velocity channel"""

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


class ad2s1210(rx_def):
    """
    AD2S1210 resolver to digital converter.
    """

    compatible_parts = ["ad2s1210"]
    _rx_data_device_name = "ad2s1210"
    _control_device_name = "ad2s1210"
    _complex_data = False

    def __post_init__(self):
        """Create custom position and velocity channel objects"""

        chan = self._ctrl.find_channel("angl0", False)
        if chan is None:
            raise Exception("angl0 channel not found")
        self.position = ad2s1210_position_channel(self._ctrl, "angl0")
        chan = self._ctrl.find_channel("anglvel0", False)

        if chan is None:
            raise Exception("anglvel0 channel not found")
        self.velocity = ad2s1210_velocity_channel(self._ctrl, "anglvel0")

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
