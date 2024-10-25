# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager

class _dyn_property:
    """
    Class descriptor for accessing individual attributes.

    This class provides a way to dynamically get and set attributes for a given device
    and channel. It uses the provided device and channel information to interact with
    the underlying IIO (Industrial I/O) attributes.

    Attributes:
        attr (str): The attribute name to be accessed.
        dev (object): The device object associated with the attribute.
        channel_name (str): The name of the channel associated with the attribute.
        output (bool): A flag indicating whether the attribute is an output.

    Methods:
        __get__(instance, owner):
            Retrieves the value of the attribute from the device.

        __set__(instance, value):
            Sets the value of the attribute on the device.
    """
    """ Class descriptor for accessing individual attributes """

    def __init__(self, attr, dev, channel_name, output):
        self._dev = dev
        self._attr = attr
        self._channel_name = channel_name
        self._output = output

    def __get__(self, instance, owner):
        return instance._get_iio_attr(
            self._channel_name, self._attr, self._output, self._dev
        )

    def __set__(self, instance, value):
        instance._set_iio_attr_int(
            self._channel_name, self._attr, self._output, int(value), self._dev
        )


class adf4030(attribute, context_manager):
    """
    ADF4030 Class

    This class provides an interface to the ADF4030 device using the IIO framework. It inherits from `attribute` and `context_manager` classes.

    Attributes:
        _device_name (str): The name of the device.
        _ctrl: The control device object.

    Methods:
        __init__(uri="", name="adf4030"):
            Initializes the ADF4030 device with the given URI and name.

            Args:
                uri (str): The URI of the device context.
                name (str): The name of the device.

            Raises:
                Exception: If no device is found with the given name.

        status:
            Returns the JESD204 device status information.

            Returns:
                str: The JESD204 device status information.
    """

    _device_name = ""

    def __init__(self, uri="", name="adf4030"):
        """
        Initialize the ADF4030 device.

        Parameters:
        uri (str): The URI of the device context. Default is an empty string.
        name (str): The name of the device. Default is "adf4030".

        Raises:
        Exception: If no device is found for the given name.

        This method initializes the context manager with the given URI and device name.
        It searches for the device in the context and sets up dynamic properties for
        each channel based on the channel attributes.
        """

        try:
            context_manager.__init__(self, uri, self._device_name)
        except Exception:
            raise Exception(f"No device found for {name}")

        self._ctrl = None

        for dev in self._ctx.devices:
            if "label" in dev.attrs and dev.attrs["label"].value == name:
                self._ctrl = dev
                break
            else:
                if dev.name == name:
                    self._ctrl = dev
                    break

        if not self._ctrl:
            raise Exception(f"No device found for {name}")

        for chan in self._ctrl.channels:
            if ("label" in chan.attrs):
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_frequency",
                    _dyn_property(
                        "frequency", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_phase",
                    _dyn_property(
                        "phase", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_autoalign_enable",
                    _dyn_property(
                        "autoalign_enable", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_autoalign_iteration",
                    _dyn_property(
                        "autoalign_iteration", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_autoalign_threshold",
                    _dyn_property(
                        "autoalign_threshold", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_output_enable",
                    _dyn_property(
                        "output_enable", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )
                setattr(
                    type(self),
                    f"{chan.attrs['label'].value.lower()}_reference_channel",
                    _dyn_property(
                        "reference_channel", dev=self._ctrl, channel_name=chan.id, output=chan.output
                    ),
                )

    @property
    def status(self):
        """jesd204_device_status: Device jesd204 link status information"""
        return self._get_iio_debug_attr_str("status", self._ctrl)
