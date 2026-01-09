# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager

from .rx_tx import rx_def, shared_def, tx_def


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
    _device_index = 0  # Index when multiple devices with same name exist

    def __init__(self, device_name="", device_index=0):
        """Initialize device with common pattern.

        Args:
            device_name: Specific device name or empty for default
            device_index: Index of device when multiple devices with same name exist
        """
        if self.compatible_parts is None:
            raise Exception("compatible_parts must be defined in subclass")

        # Validate and set device name
        if not device_name:
            device_name = self.compatible_parts[0]
        else:
            if device_name not in self.compatible_parts:
                raise Exception(
                    f"Not a compatible device: {device_name}. Supported device names "
                    f"are: {','.join(self.compatible_parts)}"
                )

        # Store device_index for use in device discovery
        self._device_index = device_index

        if hasattr(self, "_control_device_name") and not self._control_device_name:
            self._control_device_name = device_name
        if hasattr(self, "_rx_data_device_name") and not self._rx_data_device_name:
            self._rx_data_device_name = device_name
        if hasattr(self, "_tx_data_device_name") and not self._tx_data_device_name:
            self._tx_data_device_name = device_name

        return device_name

    def _add_channel_instances(self):
        """Initiate channel objects for each channel in the device."""
        if self._channel_def:
            if not callable(self._channel_def):
                raise Exception("_channel_def must be a callable class")
            for ch in self._ctrl.channels:
                name = ch.id
                setattr(self, name, self._channel_def(self._ctrl, name))


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
