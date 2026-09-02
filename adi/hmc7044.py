# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.attribute import attribute
from adi.context_manager import context_manager


class hmc7044(context_manager, attribute):
    """
    hmc7044 IIO Device Interface
    This class provides a Python interface for interacting with the HMC7044
    device via the Industrial I/O (IIO) framework.
    It allows users to access and modify device and channel attributes, as well
    as perform device-specific operations.

    Attributes:
        mute_request (str): Get or set the mute request state of the device.
        reseed_request (str): Get or set the reseed request state of the device.
        reset_dividers_request (str): Get or set the reset dividers request state of the device.
        sleep_request (str): Get or set the sleep request state of the device.
        sync_pin_mode (str): Get or set the synchronization pin mode.
        sync_pin_mode_available (str): Get the available synchronization pin modes.
        sysref_request (str): Get or set the SYSREF request state of the device.
        status (str): Get the debug status of the device.

    Channel Attributes (dynamically added per channel):
        <channel_label>_frequency (int): Get or set the frequency for the specified channel.
        <channel_label>_label (str): Get or set the label for the specified channel.
        <channel_label>_phase (int): Get or set the phase for the specified channel.

    Args:
        uri (str, optional): URI of the IIO context. Defaults to "".

    Raises:
        Exception: If the HMC7044 device is not found in the IIO context.

    Usage Example:
        dev = hmc7044("ip:192.168.2.1")
        print(dev.status)
        dev.mute_request = "1"
        print(dev.altvoltage0_frequency)
    """

    _device_name = "hmc7044"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device(self._device_name)
        if not self._ctrl:
            raise Exception("hmc7044 device not found")
        self._add_channel_properties()

    def _make_channel_property(self, channel, attr):
        def getter(self):
            return self._get_iio_attr(channel, attr, True, self._ctrl)

        def setter(self, value):
            self._set_iio_attr(channel, attr, True, value, self._ctrl)

        return property(getter, setter)

    # Device attributes
    @property
    def mute_request(self):
        return self._get_iio_dev_attr("mute_request", self._ctrl)

    @mute_request.setter
    def mute_request(self, value):
        self._set_iio_dev_attr("mute_request", value, self._ctrl)

    @property
    def reseed_request(self):
        return self._get_iio_dev_attr("reseed_request", self._ctrl)

    @reseed_request.setter
    def reseed_request(self, value):
        self._set_iio_dev_attr("reseed_request", value, self._ctrl)

    @property
    def reset_dividers_request(self):
        return self._get_iio_dev_attr("reset_dividers_request", self._ctrl)

    @reset_dividers_request.setter
    def reset_dividers_request(self, value):
        self._set_iio_dev_attr("reset_dividers_request", value, self._ctrl)

    @property
    def sleep_request(self):
        return self._get_iio_dev_attr("sleep_request", self._ctrl)

    @sleep_request.setter
    def sleep_request(self, value):
        self._set_iio_dev_attr("sleep_request", value, self._ctrl)

    @property
    def sync_pin_mode(self):
        return self._get_iio_dev_attr_str("sync_pin_mode", self._ctrl)

    @sync_pin_mode.setter
    def sync_pin_mode(self, value):
        self._set_iio_dev_attr_str("sync_pin_mode", value, self._ctrl)

    @property
    def sync_pin_mode_available(self):
        return self._get_iio_dev_attr_str("sync_pin_mode_available", self._ctrl)

    @property
    def sysref_request(self):
        return self._get_iio_dev_attr("sysref_request", self._ctrl)

    @sysref_request.setter
    def sysref_request(self, value):
        self._set_iio_dev_attr("sysref_request", value, self._ctrl)

    # Debug attribute
    @property
    def status(self):
        return self._get_iio_debug_attr_str("status", self._ctrl)

    # Channel attributes
    _channel_attrs = ["frequency", "label", "phase"]

    def _add_channel_properties(self):
        for ch in self._ctrl.channels:
            if not ch._id.startswith("altvoltage"):
                continue

            if "label" in ch.attrs:
                name = ch.attrs["label"].value
            else:
                name = ch._id

            for attr in self._channel_attrs:
                prop_name = f"{name}_{attr}"
                setattr(
                    self.__class__, prop_name, self._make_channel_property(ch._id, attr)
                )
