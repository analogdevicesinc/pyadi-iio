# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Tests for the pyadi-iio MCP server."""

import asyncio
import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Stub fastmcp if not installed
# ---------------------------------------------------------------------------

if "fastmcp" not in sys.modules:

    class _StubFastMCP:
        def __init__(self, name=""):
            self.name = name
            self._tools = {}

        def tool(self):
            def decorator(func):
                self._tools[func.__name__] = func
                return func

            return decorator

        async def list_tools(self):
            class _ToolInfo:
                def __init__(self, name):
                    self.name = name

            return [_ToolInfo(name) for name in self._tools]

        def run(self):
            pass

    _fastmcp_stub = types.ModuleType("fastmcp")
    _fastmcp_stub.FastMCP = _StubFastMCP
    sys.modules["fastmcp"] = _fastmcp_stub

# ---------------------------------------------------------------------------
# Stub the adi package only if it is not already loaded (i.e. libiio is
# unavailable).  When the real adi package is present we must NOT overwrite
# its classes or sub-modules because other tests running in the same pytest
# session depend on them.
# ---------------------------------------------------------------------------

if "adi" not in sys.modules:
    _stub = types.ModuleType("adi")
    _stub.__path__ = [os.path.join(os.path.dirname(__file__), os.pardir, "adi")]
    _stub.__package__ = "adi"

    class _MockDeviceBase:
        """A minimal mock base class used for introspection tests."""

        pass

    _MockAd9361 = type("ad9361", (_MockDeviceBase,), {"__module__": "adi.ad936x"})
    _MockPluto = type("Pluto", (_MockDeviceBase,), {"__module__": "adi.ad936x"})
    _MockAd9084 = type("ad9084", (_MockDeviceBase,), {"__module__": "adi.ad9084"})

    _stub.ad9361 = _MockAd9361
    _stub.Pluto = _MockPluto
    _stub.ad9084 = _MockAd9084
    sys.modules["adi"] = _stub

    # Stub sub-modules that the MCP server lazily imports
    for mod_name in ("adi.ad9084", "adi.ad936x", "adi.rx_tx", "adi.dds"):
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)

    _rx_core_stub = type("rx_core", (), {})
    _tx_core_stub = type("tx_core", (), {})
    _dds_stub = type("dds", (), {})
    sys.modules["adi.rx_tx"].rx_core = _rx_core_stub
    sys.modules["adi.rx_tx"].tx_core = _tx_core_stub
    sys.modules["adi.dds"].dds = _dds_stub

# Now import the MCP server module
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


def _make_mock_device(has_rx=True, has_tx=True, has_dds=True, properties=None):
    """Create a mock device with controllable introspection results."""
    device = MagicMock()
    capabilities = {
        "has_rx": has_rx,
        "has_tx": has_tx,
        "has_dds": has_dds,
        "properties": properties or {},
    }
    return device, capabilities


def _register_mock_device(uri="ip:192.168.2.1", device_class="ad9361", **device_kwargs):
    """Create and register a mock device, returning (connection_id, device, capabilities)."""
    device, capabilities = _make_mock_device(**device_kwargs)
    conn_id = mcp_mod.connection_manager.create(uri, device, device_class, capabilities)
    return conn_id, device, capabilities


class TestServerHasTools:
    """Verify the MCP server registers all expected tools."""

    def test_server_has_tools(self):
        tools = _run(mcp_mod.mcp.list_tools())
        tool_names = {t.name for t in tools}
        expected = {
            "list_device_classes",
            "connect_device",
            "disconnect_device",
            "discover_device_capabilities",
            "get_property",
            "set_property",
            "capture_rx_data",
            "configure_dds",
        }
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


class TestConnectionManagerLifecycle:
    """Test ConnectionManager create -> get -> get_info -> list -> remove."""

    def test_lifecycle(self):
        mgr = mcp_mod.ConnectionManager()
        mock_device = MagicMock()
        capabilities = {
            "has_rx": True,
            "has_tx": False,
            "has_dds": False,
            "properties": {},
        }

        # Create
        conn_id = mgr.create("ip:192.168.2.1", mock_device, "ad9361", capabilities)
        assert isinstance(conn_id, str)
        assert len(conn_id) == 36

        # Get
        device = mgr.get(conn_id)
        assert device is mock_device

        # Get info
        info = mgr.get_info(conn_id)
        assert info["device_class_name"] == "ad9361"
        assert info["capabilities"] == capabilities

        # List
        sessions = mgr.list_connections()
        assert conn_id in sessions
        assert sessions[conn_id]["uri"] == "ip:192.168.2.1"
        assert sessions[conn_id]["device_class"] == "ad9361"

        # Remove
        mgr.remove(conn_id)
        assert conn_id not in mgr.connections

    def test_get_invalid_id_raises(self):
        mgr = mcp_mod.ConnectionManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.get("nonexistent-id")


class TestListDeviceClasses:
    """Test list_device_classes tool."""

    def test_list_returns_classes(self):
        result = json.loads(_run(mcp_mod.list_device_classes()))
        assert result["status"] == "success"
        assert "ad9361" in result["device_classes"]
        assert "Pluto" in result["device_classes"]
        assert result["count"] >= 3

    def test_list_with_filter(self):
        result = json.loads(_run(mcp_mod.list_device_classes(filter_text="pluto")))
        assert result["status"] == "success"
        assert "Pluto" in result["device_classes"]
        assert "ad9361" not in result["device_classes"]


class TestConnectDevice:
    """Test connect_device tool."""

    def test_connect_success(self):
        mock_device = MagicMock()

        with patch.object(mcp_mod, "_create_device", return_value=mock_device):
            with patch.object(
                mcp_mod,
                "_introspect_device",
                return_value={
                    "has_rx": True,
                    "has_tx": True,
                    "has_dds": True,
                    "properties": {
                        "rx_lo": {"readable": True, "writable": True, "doc": ""}
                    },
                },
            ):
                result = json.loads(
                    _run(
                        mcp_mod.connect_device(
                            device_class="ad9361", uri="ip:192.168.2.1"
                        )
                    )
                )

        assert result["status"] == "success"
        assert "connection_id" in result
        assert result["device_class"] == "ad9361"
        assert result["capabilities"]["has_rx"] is True
        assert result["capabilities"]["property_count"] == 1

    def test_connect_with_kwargs(self):
        mock_device = MagicMock()

        with patch.object(
            mcp_mod, "_create_device", return_value=mock_device
        ) as mock_create:
            with patch.object(
                mcp_mod,
                "_introspect_device",
                return_value={
                    "has_rx": True,
                    "has_tx": True,
                    "has_dds": True,
                    "properties": {},
                },
            ):
                _run(
                    mcp_mod.connect_device(
                        device_class="ad9084",
                        uri="ip:192.168.2.1",
                        kwargs='{"rx1_device_name": "custom-rx"}',
                    )
                )

        mock_create.assert_called_once_with(
            "ad9084", "ip:192.168.2.1", rx1_device_name="custom-rx"
        )

    def test_connect_invalid_uri(self):
        with patch.object(
            mcp_mod, "_create_device", side_effect=Exception("No IIO context")
        ):
            result = json.loads(
                _run(mcp_mod.connect_device(device_class="ad9361", uri="ip:0.0.0.0"))
            )
        assert result["status"] == "error"
        assert "No IIO context" in result["error"]


class TestDisconnectDevice:
    """Test disconnect_device tool."""

    def test_disconnect_success(self):
        conn_id, _, _ = _register_mock_device()
        result = json.loads(_run(mcp_mod.disconnect_device(conn_id)))
        assert result["status"] == "success"
        assert conn_id not in mcp_mod.connection_manager.connections

    def test_disconnect_invalid_id(self):
        result = json.loads(_run(mcp_mod.disconnect_device("nonexistent")))
        assert result["status"] == "error"


class TestDiscoverCapabilities:
    """Test discover_device_capabilities tool."""

    def test_discover_all(self):
        props = {
            "rx_lo": {"readable": True, "writable": True, "doc": "RX LO frequency"},
            "tx_lo": {"readable": True, "writable": True, "doc": "TX LO frequency"},
            "sample_rate": {"readable": True, "writable": False, "doc": "Sample rate"},
        }
        conn_id, _, _ = _register_mock_device(properties=props)
        result = json.loads(_run(mcp_mod.discover_device_capabilities(conn_id)))

        assert result["status"] == "success"
        assert result["device_class"] == "ad9361"
        assert result["has_rx"] is True
        assert result["property_count"] == 3
        assert "rx_lo" in result["properties"]

    def test_discover_with_filter(self):
        props = {
            "rx_lo": {"readable": True, "writable": True, "doc": ""},
            "tx_lo": {"readable": True, "writable": True, "doc": ""},
        }
        conn_id, _, _ = _register_mock_device(properties=props)
        result = json.loads(
            _run(mcp_mod.discover_device_capabilities(conn_id, filter_text="rx"))
        )

        assert result["property_count"] == 1
        assert "rx_lo" in result["properties"]
        assert "tx_lo" not in result["properties"]


class TestGetProperty:
    """Test get_property tool."""

    def test_get_property_success(self):
        props = {"rx_lo": {"readable": True, "writable": True, "doc": ""}}
        conn_id, device, _ = _register_mock_device(properties=props)
        device.rx_lo = 2400000000

        result = json.loads(_run(mcp_mod.get_property(conn_id, "rx_lo")))
        assert result["status"] == "success"
        assert result["property"] == "rx_lo"
        assert result["value"] == 2400000000

    def test_get_private_property_rejected(self):
        conn_id, _, _ = _register_mock_device()
        result = json.loads(_run(mcp_mod.get_property(conn_id, "_ctrl")))
        assert result["status"] == "error"
        assert "private" in result["error"].lower()

    def test_get_unknown_property(self):
        conn_id, _, _ = _register_mock_device(properties={})
        result = json.loads(_run(mcp_mod.get_property(conn_id, "nonexistent")))
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_get_write_only_property(self):
        props = {"profile": {"readable": False, "writable": True, "doc": ""}}
        conn_id, _, _ = _register_mock_device(properties=props)
        result = json.loads(_run(mcp_mod.get_property(conn_id, "profile")))
        assert result["status"] == "error"
        assert "not readable" in result["error"].lower()


class TestSetProperty:
    """Test set_property tool."""

    def test_set_property_success(self):
        props = {"rx_lo": {"readable": True, "writable": True, "doc": ""}}
        conn_id, device, _ = _register_mock_device(properties=props)
        device.rx_lo = 0

        result = json.loads(_run(mcp_mod.set_property(conn_id, "rx_lo", "2400000000")))
        assert result["status"] == "success"
        assert result["property"] == "rx_lo"

    def test_set_list_value(self):
        props = {
            "rx_channel_nco_frequencies": {
                "readable": True,
                "writable": True,
                "doc": "",
            }
        }
        conn_id, device, _ = _register_mock_device(properties=props)

        result = json.loads(
            _run(
                mcp_mod.set_property(
                    conn_id, "rx_channel_nco_frequencies", "[100000000, 200000000]"
                )
            )
        )
        assert result["status"] == "success"

    def test_set_read_only_property(self):
        props = {"chip_version": {"readable": True, "writable": False, "doc": ""}}
        conn_id, _, _ = _register_mock_device(properties=props)
        result = json.loads(_run(mcp_mod.set_property(conn_id, "chip_version", '"v2"')))
        assert result["status"] == "error"
        assert "not writable" in result["error"].lower()

    def test_set_invalid_json(self):
        props = {"rx_lo": {"readable": True, "writable": True, "doc": ""}}
        conn_id, _, _ = _register_mock_device(properties=props)
        result = json.loads(_run(mcp_mod.set_property(conn_id, "rx_lo", "not-json")))
        assert result["status"] == "error"
        assert "invalid json" in result["error"].lower()

    def test_set_private_property_rejected(self):
        conn_id, _, _ = _register_mock_device()
        result = json.loads(_run(mcp_mod.set_property(conn_id, "_ctrl", '"foo"')))
        assert result["status"] == "error"
        assert "private" in result["error"].lower()


class TestCaptureRxData:
    """Test capture_rx_data with a mocked device."""

    def test_capture_success(self):
        props = {}
        conn_id, device, _ = _register_mock_device(has_rx=True, properties=props)
        device.rx.return_value = np.array(
            [0.1 + 0.2j, 0.3 + 0.4j, 0.5 + 0.6j], dtype=np.complex128
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "capture.npy")
            result = json.loads(
                _run(
                    mcp_mod.capture_rx_data(
                        connection_id=conn_id,
                        output_path=output_path,
                        buffer_size=1024,
                    )
                )
            )

            assert result["status"] == "success"
            assert os.path.exists(result["npy_path"])
            saved = np.load(result["npy_path"])
            np.testing.assert_array_equal(saved, device.rx.return_value)

    def test_capture_no_rx_capability(self):
        conn_id, _, _ = _register_mock_device(has_rx=False)
        result = json.loads(
            _run(
                mcp_mod.capture_rx_data(
                    connection_id=conn_id, output_path="/tmp/test.npy",
                )
            )
        )
        assert result["status"] == "error"
        assert "RX" in result["error"]


class TestConfigureDds:
    """Test configure_dds with a mocked device."""

    def test_configure_dds_success(self):
        conn_id, device, _ = _register_mock_device(has_dds=True)
        result = json.loads(
            _run(
                mcp_mod.configure_dds(
                    connection_id=conn_id, frequency=5000000, scale=0.5, channel=1,
                )
            )
        )

        assert result["status"] == "success"
        assert result["configured"]["frequency"] == 5000000
        device.dds_single_tone.assert_called_once_with(5000000, 0.5, 1)

    def test_configure_dds_no_capability(self):
        conn_id, _, _ = _register_mock_device(has_dds=False)
        result = json.loads(_run(mcp_mod.configure_dds(connection_id=conn_id)))
        assert result["status"] == "error"
        assert "DDS" in result["error"]


class TestSerializeValue:
    """Test the _serialize_value helper."""

    def test_numpy_array(self):
        assert mcp_mod._serialize_value(np.array([1, 2, 3])) == [1, 2, 3]

    def test_numpy_int(self):
        assert mcp_mod._serialize_value(np.int64(42)) == 42
        assert isinstance(mcp_mod._serialize_value(np.int64(42)), int)

    def test_numpy_float(self):
        result = mcp_mod._serialize_value(np.float64(3.14))
        assert abs(result - 3.14) < 1e-10
        assert isinstance(result, float)

    def test_primitives_passthrough(self):
        assert mcp_mod._serialize_value("hello") == "hello"
        assert mcp_mod._serialize_value(42) == 42
        assert mcp_mod._serialize_value(None) is None

    def test_nested_list(self):
        assert mcp_mod._serialize_value([np.int64(1), np.int64(2)]) == [1, 2]

    def test_unknown_type_to_str(self):
        result = mcp_mod._serialize_value(object())
        assert isinstance(result, str)
