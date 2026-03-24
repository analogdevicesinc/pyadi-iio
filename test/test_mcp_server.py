# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Tests for the pyadi-iio MCP server."""

import asyncio
import importlib
import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Prevent adi/__init__.py from importing all device drivers (which need libiio).
# We insert a stub 'adi' package into sys.modules so that
# 'from adi.mcp_server import ...' resolves directly to adi/mcp_server.py
# without executing adi/__init__.py's heavy imports.
if "adi" not in sys.modules:
    _stub = types.ModuleType("adi")
    _stub.__path__ = [os.path.join(os.path.dirname(__file__), os.pardir, "adi")]
    _stub.__package__ = "adi"
    sys.modules["adi"] = _stub

# Also stub adi.ad9084 so the lazy import in _create_ad9084 works
if "adi.ad9084" not in sys.modules:
    _stub_ad9084 = types.ModuleType("adi.ad9084")
    _stub_ad9084.ad9084 = MagicMock()
    sys.modules["adi.ad9084"] = _stub_ad9084

# Now we can safely import the MCP server module
import adi.mcp_server as mcp_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_connection_manager():
    """Reset the global ConnectionManager between tests."""
    mcp_mod.connection_manager.connections.clear()
    yield
    mcp_mod.connection_manager.connections.clear()


def _run(coro):
    """Helper to run an async coroutine in tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestServerHasTools:
    """Verify the MCP server registers all expected tools."""

    def test_server_has_tools(self):
        tools = _run(mcp_mod.mcp.list_tools())
        tool_names = {t.name for t in tools}
        expected = {
            "connect_ad9084",
            "get_device_status",
            "configure_ncos",
            "capture_rx_data",
            "enable_tx_test_tone",
            "get_jesd_status",
        }
        assert expected.issubset(tool_names), (
            f"Missing tools: {expected - tool_names}"
        )


class TestConnectionManagerLifecycle:
    """Test ConnectionManager create -> get -> list -> cleanup."""

    def test_lifecycle(self):
        mgr = mcp_mod.ConnectionManager()
        mock_device = MagicMock()

        # Create
        conn_id = mgr.create("ip:192.168.2.1", mock_device)
        assert isinstance(conn_id, str)
        assert len(conn_id) == 36  # UUID format

        # Get
        device = mgr.get(conn_id)
        assert device is mock_device

        # List
        sessions = mgr.list_connections()
        assert conn_id in sessions
        assert sessions[conn_id]["uri"] == "ip:192.168.2.1"

        # Cleanup
        mgr.remove(conn_id)
        assert conn_id not in mgr.connections

    def test_get_invalid_id_raises(self):
        mgr = mcp_mod.ConnectionManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.get("nonexistent-id")


class TestCaptureRxDataMock:
    """Test capture_rx_data with a mocked ad9084 device."""

    def test_capture_rx_data_mock(self):
        mock_device = MagicMock()
        # Simulate rx() returning complex I/Q samples
        mock_device.rx.return_value = np.array(
            [0.1 + 0.2j, 0.3 + 0.4j, 0.5 + 0.6j], dtype=np.complex128
        )
        mock_device.rx_buffer_size = 2**16
        mock_device.rx_enabled_channels = [0, 1]

        conn_id = mcp_mod.connection_manager.create("ip:192.168.2.1", mock_device)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "capture.npy")
            result_json = _run(
                mcp_mod.capture_rx_data(
                    connection_id=conn_id,
                    output_path=output_path,
                    buffer_size=1024,
                )
            )
            result = json.loads(result_json)

            assert result["status"] == "success"
            assert os.path.exists(result["npy_path"])

            # Verify the saved data matches
            saved = np.load(result["npy_path"])
            np.testing.assert_array_equal(saved, mock_device.rx.return_value)


class TestConfigureNcosMock:
    """Test configure_ncos with a mocked ad9084 device."""

    def test_configure_ncos_sets_properties(self):
        mock_device = MagicMock()
        conn_id = mcp_mod.connection_manager.create("ip:192.168.2.1", mock_device)

        rx_channel_nco = [100000000, 200000000]
        rx_main_nco = [1000000000]
        tx_channel_nco = [150000000, 250000000]
        tx_main_nco = [2000000000]

        result_json = _run(
            mcp_mod.configure_ncos(
                connection_id=conn_id,
                rx_channel_nco_frequencies=rx_channel_nco,
                rx_main_nco_frequencies=rx_main_nco,
                tx_channel_nco_frequencies=tx_channel_nco,
                tx_main_nco_frequencies=tx_main_nco,
            )
        )
        result = json.loads(result_json)

        assert result["status"] == "success"

        # Verify properties were set on the mock
        assert mock_device.rx_channel_nco_frequencies == rx_channel_nco
        assert mock_device.rx_main_nco_frequencies == rx_main_nco
        assert mock_device.tx_channel_nco_frequencies == tx_channel_nco
        assert mock_device.tx_main_nco_frequencies == tx_main_nco


class TestGetJesdStatusMock:
    """Test get_jesd_status response structure."""

    def test_get_jesd_status_structure(self):
        mock_device = MagicMock()
        mock_device.jesd204_fsm_state = "DATA"
        mock_device.jesd204_fsm_error = 0
        mock_device.jesd204_fsm_paused = 0
        mock_device.jesd204_device_status = (
            "JRX 204C Link0: Link is good\nJTX 204C Link0: Link is good"
        )

        conn_id = mcp_mod.connection_manager.create("ip:192.168.2.1", mock_device)

        result_json = _run(mcp_mod.get_jesd_status(connection_id=conn_id))
        result = json.loads(result_json)

        assert result["status"] == "success"
        assert "jesd_status" in result
        status = result["jesd_status"]
        assert "fsm_state" in status
        assert "fsm_error" in status
        assert "device_status" in status


class TestConnectInvalidUri:
    """Test connect_ad9084 with an unreachable URI returns an error."""

    def test_connect_invalid_uri(self):
        # Patch the _create_ad9084 helper to simulate connection failure
        with patch.object(
            mcp_mod, "_create_ad9084", side_effect=Exception("No IIO context")
        ):
            result_json = _run(mcp_mod.connect_ad9084(uri="ip:0.0.0.0"))
            result = json.loads(result_json)
            assert result["status"] == "error"
            assert "error" in result


class TestEnableTxTestTone:
    """Test enable_tx_test_tone with a mocked ad9084 device."""

    def test_enable_tx_test_tone(self):
        mock_device = MagicMock()
        conn_id = mcp_mod.connection_manager.create("ip:192.168.2.1", mock_device)

        result_json = _run(
            mcp_mod.enable_tx_test_tone(
                connection_id=conn_id,
                channel_nco_frequencies=[100000000],
                channel_nco_test_tone_scales=[0.5],
            )
        )
        result = json.loads(result_json)

        assert result["status"] == "success"
        assert mock_device.tx_channel_nco_frequencies == [100000000]
        assert mock_device.tx_channel_nco_test_tone_scales == [0.5]
