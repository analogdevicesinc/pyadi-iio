# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import inspect
from typing import Type, TypeVar

from .rx_tx import rx_def, rx_def_no_buff, shared_def, tx_def, tx_def_no_buff

C = TypeVar("C")


class device_base(shared_def):
    """Base class for device initialization patterns.

    This class encapsulates the common device initialization pattern used across
    many device classes in pyadi-iio. It handles:
    - Device discovery and validation
    - Channel initialization
    - Setting up _ctrl, _rxadc, or _txdac references
    - Populating channel name lists
    """

    compatible_parts = None  # To be defined in subclasses
    _control_device_name = None  # Set through device_base.__init__
    _complex_data = None  # To be defined in subclasses
    _device_index = 0  # Index when multiple devices with same name exist
    _ignore_channels = []  # List of channel names to ignore during initialization

    @staticmethod
    def variant(cls: Type[C], compatible: str = "", **chip_info) -> Type[C]:
        """Creates a new class that inherits from the given class and is marked
        as compatible with a specific device name. This allows for creating a
        class instance that constraints the search behavior of the constructor
        to a specific compatible device. Example:

        .. code-block:: python

            class adxxxx(attribute, device_base):
                def __init__(self, uri="", device_name=""):
                    device_base.__init__(self, device_name=device_name, uri=uri)


            adxx10 = device_base.variant(adxxxx, "adxx10")
            adxx20 = device_base.variant(adxxxx, "adxx20")
            dev_xx = adxxxx(uri)  # searches for all compatible devices in the context
            dev_10 = adxx10(uri)  # searches only for devices compatible with "adxx10"

        Args:
            cls:
                The class to inherit from. This should be a class that inherits
                from compatible.
            compatible:
                The name of the compatible device. This should be one of the
                names listed in the compatible_parts
            chip_info:
                Per-part attributes applied to the instance at construction time.
                Stored in the base class _device_info dict and set on the object
                after the compatible device is found in the IIO context.
        """
        if not compatible or not isinstance(compatible, str):
            raise Exception("compatible argument must be a non-empty string")

        if not issubclass(cls, device_base):
            raise TypeError(f"{cls.__name__} must inherit from device_base")

        if "compatible_parts" not in cls.__dict__:
            cls.compatible_parts = []
        if "_device_info" not in cls.__dict__:
            cls._device_info = {}

        if compatible not in cls.compatible_parts:
            cls.compatible_parts.append(compatible)
            if chip_info:
                cls._device_info[compatible] = chip_info

        return type(
            compatible,
            (cls,),
            {
                "_device_name": compatible,
                "__module__": inspect.stack()[1].frame.f_globals["__name__"],
            },
        )

    def __init__(self, device_name="", device_index=0, uri=""):
        """Initialize device with common pattern.

        Args:
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
            uri: optional URI, if provided, context and control device will be initialized
        """
        if self.compatible_parts is None:
            raise Exception("compatible_parts must be defined in subclass")

        # _device_name is used as a hint in context_manager to resolve a context
        if self._device_name:
            if self._device_name not in self.compatible_parts:
                raise Exception(
                    f"_device_name ({self._device_name}) is not a compatible part"
                )
            compatibles2check = [self._device_name]
        else:
            compatibles2check = self.compatible_parts
            if len(compatibles2check) == 1:
                self._device_name = compatibles2check[0]

        # Store device_index for use in device discovery
        self._device_index = device_index

        if hasattr(self, "_control_device_name") and not self._control_device_name:
            self._control_device_name = device_name

        if uri:
            # if uri is provided shared_def can be initialized here.
            # In this case, device_name can be a label or device ID.
            shared_def.__init__(self, uri=uri)

            if not hasattr(self, "_ctrl"):
                # self._ctrl is not resolved with self._control_device_name
                # here we try all applicable compatible parts
                self._ctrl = None
                for device in self._ctx.devices:
                    if device.name in compatibles2check:
                        self._ctrl = device
                        break

                if not self._ctrl:
                    raise Exception(
                        f"No device ({', '.join(compatibles2check)}) found in the context"
                    )

            elif self._ctrl.name not in compatibles2check:
                raise Exception(f"{self._ctrl.name} is not a compatible part")

            # normalize to resolved name
            device_name = self._ctrl.name
            self._control_device_name = device_name
        else:
            # Validate and set device name
            if not device_name:
                if self._device_name:
                    device_name = self._device_name
                else:
                    device_name = compatibles2check[0]
            else:
                if device_name not in compatibles2check:
                    raise Exception(
                        f"Not a compatible device: {device_name}. Supported device names "
                        f"are: {','.join(compatibles2check)}"
                    )

        if not self._control_device_name:
            self._control_device_name = device_name
        if hasattr(self, "_rx_data_device_name") and not self._rx_data_device_name:
            self._rx_data_device_name = device_name
        if hasattr(self, "_tx_data_device_name") and not self._tx_data_device_name:
            self._tx_data_device_name = device_name

        # apply compatible-specific info to the device instance
        info = getattr(self.__class__, "_device_info", {}).get(device_name, {})
        for k, v in info.items():
            setattr(self, k, v)

    def _add_channel_instances(self):
        """Initiate channel objects for each channel in the device."""
        self.channel = []  # type: ignore
        if self._channel_def:
            if isinstance(self._channel_def, dict):
                # Map channel definitions to channel objects based on channel id
                for ch in self._ctrl.channels:
                    if ch.id in self._ignore_channels:
                        continue
                    for ch_id, ch_def in self._channel_def.items():
                        if not callable(ch_def):
                            raise Exception(
                                "Channel definition must be a callable class"
                            )
                        if ch_id in ch.id:
                            setattr(self, ch.id, ch_def(self._ctrl, ch.id))
                            self.channel.append(getattr(self, ch.id))
                            break
            else:
                if not callable(self._channel_def):
                    raise Exception("_channel_def must be a callable class")
                for ch in self._ctrl.channels:
                    if ch.id in self._ignore_channels:
                        continue
                    setattr(self, ch.id, self._channel_def(self._ctrl, ch.id))
                    self.channel.append(getattr(self, ch.id))


class tx_chan_comp(tx_def, device_base):
    """Extend TX device base with complex channel object support."""

    _tx_data_device_name = None  # Set through device_base.__init__

    """Channel class definition for setattr usage."""
    _channel_def = None  # To be defined in subclasses

    def __init__(self, uri="", device_name="", device_index=0):
        """Initialize TX device with common pattern.

        Args:
            uri: Device URI string
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
        """
        device_base.__init__(self, device_name=device_name, device_index=device_index)
        tx_def.__init__(self, uri=uri)
        self._add_channel_instances()


class rx_chan_comp(rx_def, device_base):
    """Extend RX device base with complex channel object support."""

    _rx_data_device_name = None  # Set through device_base.__init__

    """Channel class definition for setattr usage."""
    _channel_def = None  # To be defined in subclasses

    def __init__(self, uri="", device_name="", device_index=0):
        """Initialize RX device with common pattern.

        Args:
            uri: Device URI string
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
        """
        device_base.__init__(self, device_name=device_name, device_index=device_index)
        rx_def.__init__(self, uri=uri)
        self._add_channel_instances()


class tx_chan_comp_no_buff(tx_def_no_buff, device_base):
    """Extend TX device base without buffer support with complex channel object support."""

    _tx_data_device_name = None  # Set through device_base.__init__

    """Channel class definition for setattr usage."""
    _channel_def = None  # To be defined in subclasses

    def __init__(self, uri="", device_name="", device_index=0):
        """Initialize TX device without buffer support with common pattern.

        Args:
            uri: Device URI string
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
        """
        device_base.__init__(self, device_name=device_name, device_index=device_index)
        tx_def_no_buff.__init__(self, uri=uri)
        self._add_channel_instances()


class rx_chan_comp_no_buff(rx_def_no_buff, device_base):
    """Extend RX device base without buffer support with complex channel object support."""

    _rx_data_device_name = None  # Set through device_base.__init__

    """Channel class definition for setattr usage."""
    _channel_def = None  # To be defined in subclasses

    def __init__(self, uri="", device_name="", device_index=0):
        """Initialize RX device without buffer support with common pattern.

        Args:
            uri: Device URI string
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
        """
        device_base.__init__(self, device_name=device_name, device_index=device_index)
        rx_def_no_buff.__init__(self, uri=uri)
        self._add_channel_instances()
