# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""MCP server for pyadi-iio — runtime AD9084 configuration and data capture."""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional

import numpy as np
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("pyadi-iio")


class ConnectionManager:
    """Manages persistent ad9084 device connections keyed by UUID."""

    def __init__(self):
        self.connections: Dict[str, dict] = {}

    def create(self, uri: str, device: object) -> str:
        """Register a device connection and return its UUID."""
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = {
            "device": device,
            "uri": uri,
        }
        return connection_id

    def get(self, connection_id: str) -> object:
        """Retrieve the ad9084 device instance by connection ID."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")
        return self.connections[connection_id]["device"]

    def list_connections(self) -> dict:
        """List all active connections with metadata."""
        return {
            cid: {"uri": data["uri"]}
            for cid, data in self.connections.items()
        }

    def remove(self, connection_id: str) -> None:
        """Remove a connection."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")
        del self.connections[connection_id]


connection_manager = ConnectionManager()


def _create_ad9084(uri: str, **kwargs):
    """Create an ad9084 instance (runs in thread for blocking IIO calls)."""
    from adi.ad9084 import ad9084

    return ad9084(uri=uri, **kwargs)


@mcp.tool()
async def connect_ad9084(
    uri: str,
    rx1_device_name: str = "axi-ad9084-rx-hpc",
    rx2_device_name: str = "axi-ad9084b-rx-b",
    tx1_device_name: str = "axi-ad9084-tx-hpc",
    tx2_device_name: str = "axi-ad9084-tx-b",
) -> str:
    """
    Create a connection to an AD9084 MxFE device via IIO.

    Args:
        uri: IIO URI of the target device (e.g. "ip:192.168.2.1").
        rx1_device_name: Name of RX1 device driver.
        rx2_device_name: Name of RX2 device driver.
        tx1_device_name: Name of TX1 device driver.
        tx2_device_name: Name of TX2 device driver.

    Returns:
        JSON with connection_id and device info, or error details.
    """
    try:
        device = await asyncio.to_thread(
            _create_ad9084,
            uri,
            rx1_device_name=rx1_device_name,
            rx2_device_name=rx2_device_name,
            tx1_device_name=tx1_device_name,
            tx2_device_name=tx2_device_name,
        )
        connection_id = connection_manager.create(uri, device)
        return json.dumps({
            "status": "success",
            "connection_id": connection_id,
            "uri": uri,
            "message": f"Connected to AD9084 at {uri}",
        })
    except Exception as e:
        logger.error("Failed to connect to AD9084 at %s: %s", uri, e)
        return json.dumps({
            "status": "error",
            "error": str(e),
            "uri": uri,
        })


@mcp.tool()
async def get_device_status(connection_id: str) -> str:
    """
    Read current device status including sample rates, JESD FSM state, and chip info.

    Args:
        connection_id: UUID of an active AD9084 connection.

    Returns:
        JSON with device status information.
    """
    try:
        device = connection_manager.get(connection_id)

        def _read_status():
            status = {}
            try:
                status["rx_sample_rate"] = device.rx_sample_rate
            except Exception:
                status["rx_sample_rate"] = None
            try:
                status["tx_sample_rate"] = device.tx_sample_rate
            except Exception:
                status["tx_sample_rate"] = None
            try:
                status["adc_frequency"] = device.adc_frequency
            except Exception:
                status["adc_frequency"] = None
            try:
                status["dac_frequency"] = device.dac_frequency
            except Exception:
                status["dac_frequency"] = None
            try:
                status["jesd204_fsm_state"] = device.jesd204_fsm_state
            except Exception:
                status["jesd204_fsm_state"] = None
            try:
                status["chip_version"] = device.chip_version
            except Exception:
                status["chip_version"] = None
            try:
                status["api_version"] = device.api_version
            except Exception:
                status["api_version"] = None
            return status

        status = await asyncio.to_thread(_read_status)
        return json.dumps({"status": "success", "device_status": status})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def configure_ncos(
    connection_id: str,
    rx_channel_nco_frequencies: Optional[List[int]] = None,
    rx_main_nco_frequencies: Optional[List[int]] = None,
    tx_channel_nco_frequencies: Optional[List[int]] = None,
    tx_main_nco_frequencies: Optional[List[int]] = None,
) -> str:
    """
    Configure NCO frequencies on the AD9084.

    Args:
        connection_id: UUID of an active AD9084 connection.
        rx_channel_nco_frequencies: Fine DDC NCO frequencies for RX path.
        rx_main_nco_frequencies: Coarse DDC NCO frequencies for RX path.
        tx_channel_nco_frequencies: Fine DUC NCO frequencies for TX path.
        tx_main_nco_frequencies: Coarse DUC NCO frequencies for TX path.

    Returns:
        JSON with status and configured values.
    """
    try:
        device = connection_manager.get(connection_id)

        def _configure():
            configured = {}
            if rx_channel_nco_frequencies is not None:
                device.rx_channel_nco_frequencies = rx_channel_nco_frequencies
                configured["rx_channel_nco_frequencies"] = rx_channel_nco_frequencies
            if rx_main_nco_frequencies is not None:
                device.rx_main_nco_frequencies = rx_main_nco_frequencies
                configured["rx_main_nco_frequencies"] = rx_main_nco_frequencies
            if tx_channel_nco_frequencies is not None:
                device.tx_channel_nco_frequencies = tx_channel_nco_frequencies
                configured["tx_channel_nco_frequencies"] = tx_channel_nco_frequencies
            if tx_main_nco_frequencies is not None:
                device.tx_main_nco_frequencies = tx_main_nco_frequencies
                configured["tx_main_nco_frequencies"] = tx_main_nco_frequencies
            return configured

        configured = await asyncio.to_thread(_configure)
        return json.dumps({
            "status": "success",
            "configured": configured,
            "message": "NCO frequencies configured successfully",
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def capture_rx_data(
    connection_id: str,
    output_path: str,
    buffer_size: int = 65536,
    enabled_channels: Optional[List[int]] = None,
) -> str:
    """
    Capture RX data from the AD9084 and save to a .npy file.

    Args:
        connection_id: UUID of an active AD9084 connection.
        output_path: Filesystem path where the .npy file will be saved.
        buffer_size: Number of samples to capture (default 65536).
        enabled_channels: List of channel indices to enable (default: device current setting).

    Returns:
        JSON with status, npy_path, and capture metadata.
    """
    try:
        device = connection_manager.get(connection_id)

        def _capture():
            device.rx_buffer_size = buffer_size
            if enabled_channels is not None:
                device.rx_enabled_channels = enabled_channels
            data = device.rx()
            np.save(output_path, data)
            shape = data.shape if hasattr(data, "shape") else "unknown"
            dtype = str(data.dtype) if hasattr(data, "dtype") else "unknown"
            return {"shape": str(shape), "dtype": dtype}

        meta = await asyncio.to_thread(_capture)
        return json.dumps({
            "status": "success",
            "npy_path": output_path,
            "buffer_size": buffer_size,
            "data_shape": meta["shape"],
            "data_dtype": meta["dtype"],
            "message": f"Captured {buffer_size} samples to {output_path}",
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def enable_tx_test_tone(
    connection_id: str,
    channel_nco_frequencies: Optional[List[int]] = None,
    channel_nco_test_tone_scales: Optional[List[float]] = None,
    main_nco_test_tone_en: Optional[List[int]] = None,
    channel_nco_test_tone_en: Optional[List[int]] = None,
) -> str:
    """
    Configure TX test tones on the AD9084 via NCO test tone controls.

    Args:
        connection_id: UUID of an active AD9084 connection.
        channel_nco_frequencies: Fine DUC NCO frequencies for test tone.
        channel_nco_test_tone_scales: Scale factors for channel NCO test tones.
        main_nco_test_tone_en: Enable flags for main (coarse) NCO test tones.
        channel_nco_test_tone_en: Enable flags for channel (fine) NCO test tones.

    Returns:
        JSON with status and configured tone parameters.
    """
    try:
        device = connection_manager.get(connection_id)

        def _configure_tones():
            configured = {}
            if channel_nco_frequencies is not None:
                device.tx_channel_nco_frequencies = channel_nco_frequencies
                configured["tx_channel_nco_frequencies"] = channel_nco_frequencies
            if channel_nco_test_tone_scales is not None:
                device.tx_channel_nco_test_tone_scales = channel_nco_test_tone_scales
                configured["tx_channel_nco_test_tone_scales"] = channel_nco_test_tone_scales
            if main_nco_test_tone_en is not None:
                device.tx_main_nco_test_tone_en = main_nco_test_tone_en
                configured["tx_main_nco_test_tone_en"] = main_nco_test_tone_en
            if channel_nco_test_tone_en is not None:
                device.tx_channel_nco_test_tone_en = channel_nco_test_tone_en
                configured["tx_channel_nco_test_tone_en"] = channel_nco_test_tone_en
            return configured

        configured = await asyncio.to_thread(_configure_tones)
        return json.dumps({
            "status": "success",
            "configured": configured,
            "message": "TX test tones configured successfully",
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def configure_dds(
    connection_id: str,
    frequency: int = 10000000,
    scale: float = 0.9,
    channel: int = 0,
) -> str:
    """
    Configure the DDS (Digital Direct Synthesis) to generate a single tone.

    This sets a single-tone output on the specified TX channel using the FPGA-side
    DDS. Useful for loopback testing and spectral analysis.

    Args:
        connection_id: UUID of an active AD9084 connection.
        frequency: Tone frequency in Hz (default 10 MHz). Must be < half the sample rate.
        scale: Tone scale factor in range [0, 1] (default 0.9). 1.0 is full-scale.
        channel: TX channel index (0-based, default 0).

    Returns:
        JSON with status and configured DDS parameters.
    """
    try:
        device = connection_manager.get(connection_id)

        def _configure_dds():
            device.dds_single_tone(frequency, scale, channel)
            return {
                "frequency": frequency,
                "scale": scale,
                "channel": channel,
            }

        configured = await asyncio.to_thread(_configure_dds)
        return json.dumps({
            "status": "success",
            "configured": configured,
            "message": f"DDS single tone configured: {frequency} Hz, scale {scale}, channel {channel}",
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def get_jesd_status(connection_id: str) -> str:
    """
    Get JESD204 link status from the AD9084.

    Args:
        connection_id: UUID of an active AD9084 connection.

    Returns:
        JSON with JESD FSM state, error status, and device link status.
    """
    try:
        device = connection_manager.get(connection_id)

        def _read_jesd():
            status = {}

            def _safe_read(attr_name):
                try:
                    val = getattr(device, attr_name)
                    # Ensure JSON-serializable primitive
                    if isinstance(val, (str, int, float, bool, type(None))):
                        return val
                    return str(val)
                except Exception:
                    return None

            status["fsm_state"] = _safe_read("jesd204_fsm_state")
            status["fsm_error"] = _safe_read("jesd204_fsm_error")
            status["fsm_paused"] = _safe_read("jesd204_fsm_paused")
            status["device_status"] = _safe_read("jesd204_device_status")
            try:
                status["status_check_error"] = bool(device.jesd204_device_status_check)
            except Exception:
                status["status_check_error"] = None
            return status

        jesd_status = await asyncio.to_thread(_read_jesd)
        return json.dumps({
            "status": "success",
            "jesd_status": jesd_status,
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


def main():
    """Main entry point for the pyadi-iio MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    main()
