# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4030(context_manager, attribute):
    """
    This class provides an interface to the ADF4030 device via the IIO framework.

    Args:
        uri (str, optional): URI of the IIO context. Defaults to "".

    Attributes:
        _device_name (str): Name of the IIO device ("adf4030").
        _ctrl: Reference to the IIO device controller.
        _attrs (list): List of supported channel attributes.

    Properties:
        in_temp0_input (float): Returns the temperature sensor input value.

    Dynamic Channel Properties:
        For each channel with an ID starting with "altvoltage", the following
        properties are dynamically created (where <name> is the channel label
        or ID):

            <name>_duty_cycle (float): Duty cycle of the channel.
            <name>_frequency (float): Frequency of the channel.
            <name>_label (str): Label of the channel.
            <name>_output_enable (bool): Output enable status of the channel.
            <name>_phase (float): Phase of the channel.
            <name>_reference_channel (int): Reference channel index.
            <name>_autoalign_iteration (int): Auto-align iteration value.
            <name>_autoalign_threshold (float): Auto-align threshold value.
            <name>_autoalign_threshold_en (bool): Enable/disable auto-align threshold.
            <name>_background_serial_alignment_en (bool): Enable/disable background serial alignment.
            <name>_oversampling_ratio (int): Oversampling ratio.
            <name>_oversampling_ratio_available (list): List of available oversampling ratios.

    Raises:
        Exception: If the ADF4030 device is not found in the IIO context.

    Methods:
        _make_channel_property(channel, attr): Creates a property for a given channel and attribute.
        _add_channel_properties(): Adds dynamic properties for each supported channel and attribute.

    Example:
        >>> from adi.hmc7044 import adf4030
        >>> dev = adf4030(uri="ip:192.168.2.1")
        >>> print(dev.in_temp0_input)
        >>> dev.altvoltage0_frequency = 10000000
        >>> print(dev.altvoltage0_frequency)
    """

    _device_name = "adf4030"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device(self._device_name)
        if not self._ctrl:
            raise Exception("ADF4030 device not found")
        self._add_channel_properties()

    @property
    def in_temp0_input(self):
        return self._get_iio_attr("temp0", "input", False, self._ctrl)

    def _make_channel_property(self, channel, attr):
        def getter(self):
            return self._get_iio_attr(channel, attr, True, self._ctrl)

        def setter(self, value):
            self._set_iio_attr(channel, attr, True, value, self._ctrl)

        return property(getter, setter)

    # List of channels and their attributes
    _attrs = [
        "duty_cycle",
        "frequency",
        "label",
        "output_enable",
        "phase",
        "reference_channel",
        "autoalign_iteration",
        "autoalign_threshold",
        "autoalign_threshold_en",
        "background_serial_alignment_en",
        "oversampling_ratio",
        "oversampling_ratio_available",
    ]

    def _add_channel_properties(self):
        for ch in self._ctrl.channels:
            if not ch._id.startswith("altvoltage"):
                continue

            if "label" in ch.attrs:
                name = ch.attrs["label"].value
            else:
                name = ch._id

            for attr in self._attrs:
                prop_name = f"{name}_{attr}"
                setattr(
                    self.__class__, prop_name, self._make_channel_property(ch._id, attr)
                )
