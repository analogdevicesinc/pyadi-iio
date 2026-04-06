# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""MCP server for pyadi-iio — runtime device configuration and data capture.

Provides generic tools that work with any pyadi-iio device class through
runtime introspection of device properties and capabilities.
"""

import asyncio
import inspect
import json
import logging
import uuid
from typing import Dict, Optional

import numpy as np
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("pyadi-iio")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_device_class(class_name: str):
    """Resolve a device class name to its Python class from the adi module."""
    import adi as adi_module

    cls = getattr(adi_module, class_name, None)
    if cls is None:
        raise ValueError(
            f"Unknown device class: {class_name}. "
            "Use list_device_classes to see available devices."
        )
    if not inspect.isclass(cls):
        raise ValueError(f"{class_name} is not a device class")
    return cls


def _create_device(class_name: str, uri: str, **kwargs):
    """Instantiate any pyadi-iio device class (runs in thread for blocking IIO calls)."""
    cls = _get_device_class(class_name)
    return cls(uri=uri, **kwargs)


def _introspect_device(device) -> dict:
    """Discover capabilities of a connected device via class introspection."""
    from adi.dds import dds
    from adi.rx_tx import rx_core, tx_core

    capabilities: dict = {
        "has_rx": isinstance(device, rx_core),
        "has_tx": isinstance(device, tx_core),
        "has_dds": isinstance(device, dds),
        "properties": {},
    }

    for cls in type(device).__mro__:
        for name, obj in vars(cls).items():
            if not isinstance(obj, property) or name.startswith("_"):
                continue
            if name in capabilities["properties"]:
                continue  # first in MRO wins
            doc = ""
            if obj.fget and obj.fget.__doc__:
                doc = obj.fget.__doc__.strip().split("\n")[0]
            capabilities["properties"][name] = {
                "readable": obj.fget is not None,
                "writable": obj.fset is not None,
                "doc": doc,
            }

    return capabilities


def _success(**kwargs):
    """Build a JSON success response."""
    return json.dumps(dict(status="success", **kwargs))


def _error(msg, **kwargs):
    """Build a JSON error response."""
    return json.dumps(dict(status="error", error=msg, **kwargs))


def _serialize_value(value):
    """Convert a device property value to a JSON-serializable type."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    return str(value)


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages persistent device connections keyed by UUID."""

    def __init__(self):
        self.connections: Dict[str, dict] = {}

    def create(
        self, uri, device, device_class_name, capabilities,
    ):
        """Register a device connection and return its UUID."""
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = {
            "device": device,
            "uri": uri,
            "device_class_name": device_class_name,
            "capabilities": capabilities,
        }
        return connection_id

    def get(self, connection_id):
        """Retrieve the device instance by connection ID."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")
        return self.connections[connection_id]["device"]

    def get_info(self, connection_id):
        """Retrieve the full connection dict including capabilities."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")
        return self.connections[connection_id]

    def list_connections(self):
        """List all active connections with metadata."""
        result = {}
        for cid, data in self.connections.items():
            result[cid] = {
                "uri": data["uri"],
                "device_class": data["device_class_name"],
            }
        return result

    def remove(self, connection_id):
        """Remove a connection."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")
        del self.connections[connection_id]


connection_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_device_classes(filter_text: Optional[str] = None) -> str:
    """List available pyadi-iio device classes.

    :param filter_text: Optional substring to filter class names (case-insensitive).
    :returns: JSON with a list of available device class names.
    """
    try:

        def _list():
            import adi as adi_module

            classes = []
            for name in sorted(dir(adi_module)):
                if name.startswith("_"):
                    continue
                obj = getattr(adi_module, name, None)
                if not inspect.isclass(obj):
                    continue
                if not getattr(obj, "__module__", "").startswith("adi."):
                    continue
                if filter_text and filter_text.lower() not in name.lower():
                    continue
                classes.append(name)
            return classes

        classes = await asyncio.to_thread(_list)
        return _success(device_classes=classes, count=len(classes))
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def connect_device(
    device_class: str, uri: str, kwargs: Optional[str] = None,
) -> str:
    """Create a connection to any pyadi-iio device.

    :param device_class: Name of the device class (e.g. "ad9361", "Pluto", "ad9084").
        Use list_device_classes to discover available classes.
    :param uri: IIO URI of the target device (e.g. "ip:192.168.2.1").
    :param kwargs: Optional JSON string of extra constructor keyword arguments
        (e.g. '{"rx1_device_name": "axi-ad9084-rx-hpc"}').
    :returns: JSON with connection_id and device capability summary.
    """
    try:
        extra_kwargs = {}
        if kwargs:
            extra_kwargs = json.loads(kwargs)

        def _connect():
            device = _create_device(device_class, uri, **extra_kwargs)
            capabilities = _introspect_device(device)
            return device, capabilities

        device, capabilities = await asyncio.to_thread(_connect)
        connection_id = connection_manager.create(
            uri, device, device_class, capabilities
        )

        summary = {
            "has_rx": capabilities["has_rx"],
            "has_tx": capabilities["has_tx"],
            "has_dds": capabilities["has_dds"],
            "property_count": len(capabilities["properties"]),
        }

        return _success(
            connection_id=connection_id,
            device_class=device_class,
            uri=uri,
            capabilities=summary,
            message=f"Connected to {device_class} at {uri}",
        )
    except Exception as e:
        logger.error("Failed to connect %s at %s: %s", device_class, uri, e)
        return _error(str(e), device_class=device_class, uri=uri)


@mcp.tool()
async def disconnect_device(connection_id: str) -> str:
    """Disconnect from a device and clean up the connection.

    :param connection_id: UUID of an active connection.
    :returns: JSON with status.
    """
    try:
        connection_manager.remove(connection_id)
        return _success(message=f"Disconnected {connection_id}")
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def discover_device_capabilities(
    connection_id: str, filter_text: Optional[str] = None,
) -> str:
    """Discover what a connected device supports.

    Returns RX/TX/DDS capabilities and all available properties with
    read/write metadata.

    :param connection_id: UUID of an active connection.
    :param filter_text: Optional substring to filter property names (case-insensitive).
    :returns: JSON with device capabilities and property list.
    """
    try:
        info = connection_manager.get_info(connection_id)
        capabilities = info["capabilities"]

        properties = capabilities["properties"]
        if filter_text:
            properties = {
                k: v for k, v in properties.items() if filter_text.lower() in k.lower()
            }

        return _success(
            device_class=info["device_class_name"],
            has_rx=capabilities["has_rx"],
            has_tx=capabilities["has_tx"],
            has_dds=capabilities["has_dds"],
            properties=properties,
            property_count=len(properties),
        )
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def get_property(connection_id: str, property_name: str) -> str:
    """Read a property from a connected device.

    :param connection_id: UUID of an active connection.
    :param property_name: Name of the property to read (e.g. "rx_lo", "sample_rate").
        Use discover_device_capabilities to see available properties.
    :returns: JSON with the property value.
    """
    try:
        info = connection_manager.get_info(connection_id)
        device = info["device"]
        capabilities = info["capabilities"]

        if property_name.startswith("_"):
            return _error("Cannot access private properties")

        prop_meta = capabilities["properties"].get(property_name)
        if prop_meta is None:
            return _error(
                f"Property '{property_name}' not found. "
                "Use discover_device_capabilities to see available properties."
            )
        if not prop_meta["readable"]:
            return _error(f"Property '{property_name}' is not readable")

        def _read():
            return getattr(device, property_name)

        value = await asyncio.to_thread(_read)
        return _success(property=property_name, value=_serialize_value(value),)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def set_property(connection_id: str, property_name: str, value: str,) -> str:
    """Set a property on a connected device.

    :param connection_id: UUID of an active connection.
    :param property_name: Name of the property to set (e.g. "rx_lo", "sample_rate").
        Use discover_device_capabilities to see writable properties.
    :param value: JSON-encoded value to set (e.g. "1000000000", "[100, 200]", '"auto"').
    :returns: JSON with status and the confirmed value read back from the device.
    """
    try:
        info = connection_manager.get_info(connection_id)
        device = info["device"]
        capabilities = info["capabilities"]

        if property_name.startswith("_"):
            return _error("Cannot access private properties")

        prop_meta = capabilities["properties"].get(property_name)
        if prop_meta is None:
            return _error(
                f"Property '{property_name}' not found. "
                "Use discover_device_capabilities to see available properties."
            )
        if not prop_meta["writable"]:
            return _error(f"Property '{property_name}' is not writable")

        parsed_value = json.loads(value)

        def _write():
            setattr(device, property_name, parsed_value)
            if prop_meta["readable"]:
                return getattr(device, property_name)
            return parsed_value

        confirmed = await asyncio.to_thread(_write)
        return _success(
            property=property_name,
            value=_serialize_value(confirmed),
            message=f"Set {property_name} successfully",
        )
    except json.JSONDecodeError as e:
        return _error(f"Invalid JSON value: {e}")
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def capture_rx_data(
    connection_id: str,
    output_path: str,
    buffer_size: int = 65536,
    enabled_channels: Optional[str] = None,
) -> str:
    """Capture RX data from a connected device and save to a .npy file.

    :param connection_id: UUID of an active connection.
    :param output_path: Filesystem path where the .npy file will be saved.
    :param buffer_size: Number of samples to capture (default 65536).
    :param enabled_channels: JSON list of channel indices to enable (e.g. "[0, 1]").
        Default: device current setting.
    :returns: JSON with status, npy_path, and capture metadata.
    """
    try:
        info = connection_manager.get_info(connection_id)
        device = info["device"]

        if not info["capabilities"]["has_rx"]:
            return _error("Device does not have RX capabilities")

        channels = None
        if enabled_channels is not None:
            channels = json.loads(enabled_channels)

        def _capture():
            device.rx_buffer_size = buffer_size
            if channels is not None:
                device.rx_enabled_channels = channels
            data = device.rx()
            np.save(output_path, data)
            shape = data.shape if hasattr(data, "shape") else "unknown"
            dtype = str(data.dtype) if hasattr(data, "dtype") else "unknown"
            return {"shape": str(shape), "dtype": dtype}

        meta = await asyncio.to_thread(_capture)
        return _success(
            npy_path=output_path,
            buffer_size=buffer_size,
            data_shape=meta["shape"],
            data_dtype=meta["dtype"],
            message=f"Captured {buffer_size} samples to {output_path}",
        )
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def configure_dds(
    connection_id: str, frequency: int = 10000000, scale: float = 0.9, channel: int = 0,
) -> str:
    """Configure the DDS (Digital Direct Synthesis) to generate a single tone.

    Sets a single-tone output on the specified TX channel using the FPGA-side
    DDS. Useful for loopback testing and spectral analysis.

    :param connection_id: UUID of an active connection.
    :param frequency: Tone frequency in Hz (default 10 MHz). Must be < half the sample rate.
    :param scale: Tone scale factor in range [0, 1] (default 0.9). 1.0 is full-scale.
    :param channel: TX channel index (0-based, default 0).
    :returns: JSON with status and configured DDS parameters.
    """
    try:
        info = connection_manager.get_info(connection_id)
        device = info["device"]

        if not info["capabilities"]["has_dds"]:
            return _error("Device does not have DDS capabilities")

        def _configure_dds():
            device.dds_single_tone(frequency, scale, channel)
            return {
                "frequency": frequency,
                "scale": scale,
                "channel": channel,
            }

        configured = await asyncio.to_thread(_configure_dds)
        dds_msg = f"DDS single tone configured: {frequency} Hz, scale {scale}, channel {channel}"
        return _success(configured=configured, message=dds_msg)
    except Exception as e:
        return _error(str(e))


def main():
    """Main entry point for the pyadi-iio MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    main()
