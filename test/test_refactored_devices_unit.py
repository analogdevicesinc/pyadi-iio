"""
Unit tests for refactored device classes using device_base pattern.
These tests verify the refactoring maintains correct structure and interfaces.
"""

from collections import OrderedDict
from unittest.mock import MagicMock, Mock, call, patch

import pytest

import adi
from adi.device_base import device_base, rx_chan_comp
from adi.rx_tx import shared_def


class _SharedDefTestDevice(shared_def):
    """Concrete shared_def used to test context selection."""

    @property
    def _complex_data(self):  # type: ignore[override]
        return False

    @property
    def _control_device_name(self):  # type: ignore[override]
        return "test-device"

    @property
    def _rx_data_device_name(self):
        return "test-device"


def test_shared_def_falls_back_to_ip_analog(monkeypatch):
    """URI-less construction retains the legacy ip:analog fallback."""
    device = MagicMock()
    device.name = "test-device"
    context = MagicMock()
    context.devices = [device]
    context.find_device.return_value = device

    class FakeContext:
        calls = []

        def __new__(cls, uri):
            cls.calls.append(uri)
            return context

    monkeypatch.setattr("adi.rx_tx.iio.scan_contexts", lambda: {})
    monkeypatch.setattr("adi.context_manager.iio.Context", FakeContext)

    dev = _SharedDefTestDevice()

    assert FakeContext.calls == ["ip:analog"]
    assert dev.ctx is context
    assert dev._ctrl is device


def test_ltc2378_preserves_all_compatible_parts():
    """The common-parent migration must not drop a supported device name."""
    assert "ltc2377-20" in adi.ltc2378.compatible_parts


def test_max9611_preserves_legacy_rx_channel_order():
    """Integer RX indices and returned array order remain backwards compatible."""
    assert adi.max9611._rx_channel_names == ["temp", "voltage1"]


def test_ad5710r_preserved_device_properties():
    """Exercise preserved AD5710R device-level getter and setter contracts."""
    dev = object.__new__(adi.ad5710r)
    dev._get_iio_dev_attr_str = Mock(return_value="value")
    dev._set_iio_dev_attr_str = Mock()

    assert dev.sampling_frequency == "value"
    assert dev.all_ch_input_registers == "value"
    assert dev.all_ch_raw == "value"

    dev.sampling_frequency = 1000
    dev.all_ch_input_registers = 42
    dev.all_ch_raw = 7

    assert dev._get_iio_dev_attr_str.call_args_list == [
        call("sampling_frequency"),
        call("all_ch_input_registers"),
        call("all_ch_raw"),
    ]
    assert dev._set_iio_dev_attr_str.call_args_list == [
        call("sampling_frequency", 1000),
        call("all_ch_input_registers", 42),
        call("all_ch_raw", 7),
    ]


def _mock_context(monkeypatch, device_name, channel_names, scan_elements=None):
    """Install a minimal IIO context for common-parent unit tests."""
    if scan_elements is None:
        scan_elements = [True] * len(channel_names)
    channels = []
    for name, scan_element in zip(channel_names, scan_elements):
        channel = MagicMock()
        channel.id = name
        channel._id = name
        channel.scan_element = scan_element
        channels.append(channel)
    device = MagicMock()
    device.name = device_name
    device.channels = channels
    device._channels = channels

    class FakeContext:
        def __init__(self):
            self.devices = [device]
            self.find_device = MagicMock(
                side_effect=lambda name: device if name == device_name else None
            )

    context = FakeContext()
    monkeypatch.setattr("adi.rx_tx.iio.Context", FakeContext)

    def init_context(self, uri="", device_name=""):
        self._ctx = context
        self.uri = uri

    monkeypatch.setattr("adi.rx_tx.context_manager.__init__", init_context)
    return device


def test_max31855_common_parent_preserves_aliases_and_order(monkeypatch):
    """MAX31855 keeps its driver-name mapping and public temperature aliases."""
    _mock_context(monkeypatch, "maxim_thermocouple", ["t_temp", "i_temp"])

    with adi.max31855(uri="local:") as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == ["t_temp", "i_temp"]
        assert [channel.name for channel in dev.channel] == ["t_temp", "i_temp"]
        assert dev.temp_t is dev.t_temp is dev.channel[0]
        assert dev.temp_i is dev.i_temp is dev.channel[1]


def test_ltc2983_common_parent_preserves_ordered_all_channel_api(monkeypatch):
    """LTC2983 retains OrderedDict access and includes non-scan channels."""
    _mock_context(
        monkeypatch, "ltc2983", ["voltage0", "temp1", "status"], [True, True, False],
    )

    with adi.ltc2983(uri="local:") as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == ["voltage0", "temp1", "status"]
        assert isinstance(dev.channel, OrderedDict)
        assert list(dev.channel) == ["voltage0", "temp1", "status"]
        assert [channel.name for channel in dev.channel.values()] == list(dev.channel)


def test_ltc2499_common_parent_preserves_ordered_all_channel_api(monkeypatch):
    """LTC2499 retains OrderedDict access and includes non-scan channels."""
    _mock_context(
        monkeypatch,
        "ltc2499",
        ["voltage0", "voltage1", "timestamp"],
        [True, True, False],
    )

    with adi.ltc2499(uri="local:") as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == ["voltage0", "voltage1", "timestamp"]
        assert dev.rx_enabled_channels == [0, 1]
        assert isinstance(dev.channel, OrderedDict)
        assert list(dev.channel) == ["voltage0", "voltage1", "timestamp"]
        assert [channel.name for channel in dev.channel.values()] == list(dev.channel)


def _mock_indexed_context(monkeypatch, device_name, channel_names):
    """Install a context containing two same-name devices."""
    devices = []
    for suffix in ("first", "second"):
        channels = []
        for name in channel_names:
            channel = MagicMock()
            channel.id = name
            channel._id = f"{name}_{suffix}"
            channel.scan_element = True
            channels.append(channel)
        device = MagicMock()
        device.name = device_name
        device.channels = channels
        device._channels = channels
        devices.append(device)

    class FakeContext:
        def __init__(self):
            self.devices = devices

        def find_device(self, name):
            return next((device for device in devices if device.name == name), None)

    context = FakeContext()
    monkeypatch.setattr("adi.rx_tx.iio.Context", FakeContext)

    def init_context(self, uri="", device_name=""):
        self._ctx = context
        self.uri = uri

    monkeypatch.setattr("adi.rx_tx.context_manager.__init__", init_context)
    return devices


@pytest.mark.parametrize(
    "device_class,device_name", [(adi.adpd188, "adpd188"), (adi.adpd1080, "adpd1080")],
)
def test_adpd_common_parent_preserves_index_and_private_channel_order(
    monkeypatch, device_class, device_name
):
    """ADPD migrations retain indexed discovery and private channel traversal."""
    devices = _mock_indexed_context(monkeypatch, device_name, ["red", "blue"])

    with device_class(uri="local:", device_index=1) as dev:
        assert dev._ctrl is dev._rxadc is devices[1]
        assert dev._rx_channel_names == ["red_second", "blue_second"]
        assert dev.rx_enabled_channels == [0, 1]
        assert dev.rx_buffer_size == 16
        assert [channel.name for channel in dev.channel] == dev._rx_channel_names
        assert dev.red_second is dev.channel[0]
        assert dev.blue_second is dev.channel[1]


@pytest.mark.parametrize(
    "device_class,device_name", [(adi.adpd188, "adpd188"), (adi.adpd1080, "adpd1080")],
)
def test_adpd_common_parent_rejects_missing_device_index(
    monkeypatch, device_class, device_name
):
    """Out-of-range indexed discovery raises a deterministic error."""
    _mock_indexed_context(monkeypatch, device_name, ["red"])

    with pytest.raises(Exception, match=f"{device_name} at index 2"):
        device_class(uri="local:", device_index=2)


@pytest.mark.parametrize("device_name", ["ad7745", "ad7746", "ad7747"])
def test_ad7746_common_parent_preserves_order_and_wrapper_subtypes(
    monkeypatch, device_name
):
    """AD7746 family keeps ordered mapping and ID-specific wrapper types."""
    names = ["voltage1", "capacitance1", "temp0", "status"]
    _mock_context(monkeypatch, device_name, names, [True, True, True, False])

    with adi.ad7746(uri="local:", device_name=device_name) as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == names
        assert dev.rx_enabled_channels == [0, 1, 2, 3]
        assert isinstance(dev.channel, OrderedDict)
        assert list(dev.channel) == names[:3]
        assert isinstance(dev.channel["voltage1"], adi.ad7746._volt_channel)
        assert isinstance(dev.channel["capacitance1"], adi.ad7746._cap_channel)
        assert isinstance(dev.channel["temp0"], adi.ad7746._temp_channel)


def test_ad7746_common_parent_preserves_empty_name_rejection(monkeypatch):
    """The legacy constructor does not silently default an empty device name."""
    _mock_context(monkeypatch, "ad7746", ["voltage0"])

    with pytest.raises(Exception, match="Not a compatible device: $"):
        adi.ad7746(uri="local:")


def test_ad7746_channel_subtypes_preserve_attribute_forwarding():
    """Channel-specific wrappers retain their public attribute contracts."""
    ctrl = MagicMock()
    temp = adi.ad7746._temp_channel(ctrl, "temp0")
    temp._get_iio_attr = Mock(return_value=23)
    assert temp.input == 23

    voltage = adi.ad7746._volt_channel(ctrl, "voltage0")
    voltage._get_iio_attr = Mock(return_value=11)
    voltage._get_iio_attr_str = Mock(
        side_effect=lambda _name, attr, _output: {
            "scale": "2.5",
            "sampling_frequency": "50",
            "sampling_frequency_available": "50 31 16 8",
        }[attr]
    )
    voltage._set_iio_attr = Mock()
    assert voltage.raw == 11
    assert voltage.scale == 2.5
    assert voltage.sampling_frequency == "50"
    assert voltage.sampling_frequency_available == [50, 31, 16, 8]
    voltage.sampling_frequency = 31
    voltage.calibscale_calibration()

    capacitance = adi.ad7746._cap_channel(ctrl, "capacitance0")
    capacitance._get_iio_attr = Mock(side_effect=lambda _name, attr, _output: attr)
    capacitance._get_iio_attr_str = Mock(return_value="100")
    capacitance._set_iio_attr = Mock()
    capacitance._set_iio_attr_float = Mock()
    assert capacitance.offset == "100"
    assert capacitance.calibscale == "calibscale"
    assert capacitance.calibbias == "calibbias"
    capacitance.offset = 101
    capacitance.calibscale = 1.5
    capacitance.calibbias = 2
    capacitance.calibbias_calibration()


def test_adis16460_common_parent_preserves_rx_contract(monkeypatch):
    """ADIS16460 keeps channel order and its smaller default RX buffer."""
    names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
    ]
    _mock_context(monkeypatch, "adis16460", names)

    with adi.adis16460(uri="local:") as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == names
        assert dev.rx_enabled_channels == list(range(6))
        assert dev.rx_buffer_size == 16


@pytest.mark.parametrize("device_name", ["max11205a", "max11205b"])
def test_max11205_common_parent_preserves_exact_selection(monkeypatch, device_name):
    """MAX11205 keeps explicit model selection and private-ID channel ordering."""
    _mock_context(monkeypatch, device_name, ["voltage0", "voltage1"])

    with adi.max11205(uri="local:", device_name=device_name) as dev:
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == ["voltage0", "voltage1"]
        assert dev.rx_enabled_channels == [0, 1]
        assert [channel.name for channel in dev.channel] == ["voltage0", "voltage1"]
        assert dev.voltage0 is dev.channel[0]
        assert dev.voltage1 is dev.channel[1]


def test_max11205_default_does_not_fallback_to_variant_b(monkeypatch):
    """The default remains max11205a rather than probing compatible variants."""
    _mock_context(monkeypatch, "max11205b", ["voltage0"])

    with pytest.raises(Exception, match="max11205a"):
        adi.max11205(uri="local:")


@pytest.mark.parametrize("selected_name", ["ADXL312", "ADXL313", "ADXL314"])
def test_adxl313_common_parent_preserves_family_discovery(monkeypatch, selected_name):
    """ADXL313 selects any supported family member and retains channel aliases."""
    _mock_context(monkeypatch, selected_name, ["accel_x", "accel_y", "accel_z"])

    with adi.adxl313(uri="local:") as dev:
        assert dev._device_name == selected_name
        assert dev._ctrl is dev._rxadc
        assert dev._rx_channel_names == ["accel_x", "accel_y", "accel_z"]
        assert dev.rx_enabled_channels == [0, 1, 2]
        assert [channel.name for channel in dev.channel] == dev._rx_channel_names
        assert dev.accel_x is dev.channel[0]
        assert dev.accel_y is dev.channel[1]
        assert dev.accel_z is dev.channel[2]


def test_adxl313_preserves_first_compatible_context_order(monkeypatch):
    """Family discovery remains context-ordered rather than model-prioritized."""
    channels = ["accel_x", "accel_y", "accel_z"]
    first = _mock_context(monkeypatch, "ADXL314", channels)
    second = MagicMock()
    second.name = "ADXL312"
    second.channels = first.channels

    # Expose a second compatible device in the same context.
    with patch("adi.rx_tx.context_manager.__init__") as init:

        class FakeContext:
            def __init__(self):
                self.devices = [first, second]

            def find_device(self, name):
                return next(
                    (device for device in self.devices if device.name == name), None
                )

        context = FakeContext()
        monkeypatch.setattr("adi.rx_tx.iio.Context", FakeContext)

        def set_context(instance, uri="", device_name=""):
            instance._ctx = context
            instance.uri = uri

        init.side_effect = set_context
        with adi.adxl313(uri="local:") as dev:
            assert dev._device_name == "ADXL314"
            assert dev._ctrl is first


def test_adxl313_rejects_context_without_compatible_device(monkeypatch):
    """Contexts without an ADXL312/313/314 retain the legacy error."""
    _mock_context(monkeypatch, "other-device", ["accel_x"])

    with pytest.raises(Exception, match="No compatible device found"):
        adi.adxl313(uri="local:")


@pytest.mark.parametrize(
    "device_class,requested_device",
    [(adi.adxl380, "adxl380"), (adi.adis16475, "adis16505-2"),],
)
def test_compatible_device_fallback(monkeypatch, device_class, requested_device):
    """Classes that historically probed compatible parts must keep doing so."""
    attempts = []

    def init_with_first_device_missing(self, uri="", device_name="", device_index=0):
        attempts.append(device_name)
        if len(attempts) == 1:
            raise Exception(f"No device found with name {device_name}")

    monkeypatch.setattr(rx_chan_comp, "__init__", init_with_first_device_missing)

    device_class(uri="local:", device_name=requested_device)

    assert attempts == [
        requested_device,
        next(
            part for part in device_class.compatible_parts if part != requested_device
        ),
    ]


class _ConcreteChannelDefDevice(device_base):
    """Concrete device_base used to exercise _add_channel_instances directly."""

    @property
    def _complex_data(self):  # type: ignore[override]
        return False


class _RecordingChannel:
    """Minimal channel wrapper recording the ctrl/name it was built with."""

    def __init__(self, ctrl, name):
        self.ctrl = ctrl
        self.name = name


class _OtherChannel(_RecordingChannel):
    """Second channel type used to verify id-based class selection."""


def _channel_def_device(channel_ids, channel_def, ignore_channels=None):
    """Build a device_base instance ready for _add_channel_instances().

    Bypasses device discovery: only the pieces _add_channel_instances touches
    (``_ctrl.channels``, ``_channel_def`` and ``_ignore_channels``) are wired up.
    """
    dev = object.__new__(_ConcreteChannelDefDevice)
    ctrl = MagicMock()
    channels = []
    for cid in channel_ids:
        channel = MagicMock()
        channel.id = cid
        channels.append(channel)
    ctrl.channels = channels
    dev._ctrl = ctrl
    dev._channel_def = channel_def
    dev._ignore_channels = ignore_channels if ignore_channels is not None else []
    return dev


def test_channel_def_dict_maps_ids_to_matching_classes():
    """A dict _channel_def picks the class whose key is a substring of the id."""
    dev = _channel_def_device(
        ["voltage0", "voltage1", "temp0"],
        {"voltage": _RecordingChannel, "temp": _OtherChannel},
    )

    dev._add_channel_instances()

    assert [ch.name for ch in dev.channel] == ["voltage0", "voltage1", "temp0"]
    assert isinstance(dev.voltage0, _RecordingChannel)
    assert isinstance(dev.voltage1, _RecordingChannel)
    assert isinstance(dev.temp0, _OtherChannel)
    # Each channel is exposed as a named attribute pointing at the same object.
    assert dev.voltage0 is dev.channel[0]
    assert dev.temp0 is dev.channel[2]
    # Wrapper classes are constructed with the shared ctrl and the channel id.
    assert dev.voltage0.ctrl is dev._ctrl
    assert dev.voltage0.name == "voltage0"


def test_channel_def_dict_uses_first_matching_key():
    """When several keys match an id, the first in insertion order wins."""
    dev = _channel_def_device(
        ["voltage0"],
        OrderedDict([("voltage", _RecordingChannel), ("voltage0", _OtherChannel)]),
    )

    dev._add_channel_instances()

    assert isinstance(dev.voltage0, _RecordingChannel)


def test_channel_def_dict_skips_unmatched_channels():
    """Channels with no matching key are left out of the channel list."""
    dev = _channel_def_device(["voltage0", "current0"], {"voltage": _RecordingChannel},)

    dev._add_channel_instances()

    assert [ch.name for ch in dev.channel] == ["voltage0"]
    assert not hasattr(dev, "current0")


def test_channel_def_dict_honors_ignore_channels():
    """Ignored channel ids are skipped before any class matching happens."""
    dev = _channel_def_device(
        ["voltage0", "voltage1"],
        {"voltage": _RecordingChannel},
        ignore_channels=["voltage1"],
    )

    dev._add_channel_instances()

    assert [ch.name for ch in dev.channel] == ["voltage0"]
    assert not hasattr(dev, "voltage1")


def test_channel_def_dict_rejects_non_callable_value():
    """A non-callable dict value raises a descriptive error."""
    dev = _channel_def_device(["voltage0"], {"voltage": "not-callable"})

    with pytest.raises(Exception, match="Channel definition must be a callable class"):
        dev._add_channel_instances()


def test_channel_def_callable_preserves_legacy_behavior():
    """A single callable _channel_def still builds every non-ignored channel."""
    dev = _channel_def_device(
        ["voltage0", "voltage1", "temp0"], _RecordingChannel, ignore_channels=["temp0"],
    )

    dev._add_channel_instances()

    assert [ch.name for ch in dev.channel] == ["voltage0", "voltage1"]
    assert all(isinstance(ch, _RecordingChannel) for ch in dev.channel)
    assert dev.voltage0 is dev.channel[0]


def test_channel_def_callable_rejects_non_callable_value():
    """The legacy branch still rejects a non-callable _channel_def."""
    dev = _channel_def_device(["voltage0"], "not-callable")

    with pytest.raises(Exception, match="_channel_def must be a callable class"):
        dev._add_channel_instances()


def channel_definitions(device_class, iio_uri):
    with eval(f"adi.{device_class}(uri=iio_uri)") as dev:
        assert hasattr(dev, "channel"), f"{device_class} missing channel attribute"
        assert isinstance(
            dev.channel, list
        ), f"{device_class} channel attribute is not a list"
        assert len(dev.channel) > 0, f"{device_class} has no channels defined"
        for ch in dev.channel:
            # assert hasattr(
            #     ch, "raw"
            # ), f"{device_class} channel {ch.name} missing raw property"
            assert hasattr(
                ch, "scale"
            ), f"{device_class} channel {ch.name} missing scale property"
            # device_base exposes each channel as a named attribute on the
            # device (the documented ``device.<channel>.<attr>`` contract).
            assert getattr(dev, ch.name, None) is ch, (
                f"{device_class} channel {ch.name} not accessible as a named "
                "attribute on the device"
            )


@pytest.fixture()
def test_channel_definitions(request):
    yield channel_definitions


@pytest.mark.iio_hardware("ad7124-8")
@pytest.mark.parametrize("device_class", ["ad7124"])
def test_ad7124_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7490")
@pytest.mark.parametrize("device_class", ["ad7490"])
def test_ad7490_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7091r-8")
@pytest.mark.parametrize("device_class", ["ad7091rx"])
def test_ad7091rx_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7770")
@pytest.mark.parametrize("device_class", ["ad777x"])
def test_ad777x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7405")
@pytest.mark.parametrize("device_class", ["ad7405"])
def test_ad7405_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7134", True)  # Bad emulation file
@pytest.mark.parametrize("device_class", ["ad7134"])
def test_ad7134_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4020", True)  # Bad emulation file (missing scale value)
@pytest.mark.parametrize("device_class", ["ad4020"])
def test_ad4020_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4080")
@pytest.mark.parametrize("device_class", ["ad4080"])
def test_ad4080_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4170")
@pytest.mark.parametrize("device_class", ["ad4170"])
def test_ad4170_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad738x")
@pytest.mark.parametrize("device_class", ["ad738x"])
def test_ad738x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad405x", True)  # Bad emulation file
@pytest.mark.parametrize("device_class", ["ad405x"])
def test_ad405x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4858")
@pytest.mark.parametrize("device_class", ["ad4858"])
def test_ad4858_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad579x")
@pytest.mark.parametrize("device_class", ["ad579x"])
def test_ad579x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5754r")
@pytest.mark.parametrize("device_class", ["ad5754r"])
def test_ad5754r_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ltc2314-14", True)
@pytest.mark.parametrize("device_class", ["ltc2314_14"])
def test_ltc2314_14_channel_definitions(
    test_channel_definitions, iio_uri, device_class
):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5686", True)
@pytest.mark.parametrize("device_class", ["ad5686"])
def test_ad5686_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7291", True)
@pytest.mark.parametrize("device_class", ["ad7291"])
def test_ad7291_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ltc2378-20")
@pytest.mark.parametrize("device_class", ["ltc2378"])
def test_ltc2378_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("max14001")
@pytest.mark.parametrize("device_class", ["max14001"])
def test_max14001_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ada4355")
@pytest.mark.parametrize("device_class", ["ada4355"])
def test_ada4355_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("adxrs290")
@pytest.mark.parametrize("device_class", ["adxrs290"])
def test_adxrs290_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("adxl380")
@pytest.mark.parametrize("device_class", ["adxl380"])
def test_adxl380_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5706r")
@pytest.mark.parametrize("device_class", ["ad5706r"])
def test_ad5706r_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad3552r_hs")
@pytest.mark.parametrize("device_class", ["ad3552r_hs"])
def test_ad3552r_hs_channel_definitions(
    test_channel_definitions, iio_uri, device_class
):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("max31865")
@pytest.mark.parametrize("device_class", ["max31865"])
def test_max31865_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("max9611")
@pytest.mark.parametrize("device_class", ["max9611"])
def test_max9611_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware(
    "adis16475", True
)  # iio-emu does not support trigger assignment used in device init
@pytest.mark.parametrize("device_class", ["adis16475"])
def test_adis16475_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5710r")
@pytest.mark.parametrize("device_class", ["ad5710r"])
def test_ad5710r_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)
    with adi.ad5710r(uri=iio_uri) as dev:
        expected_names = [ch.id for ch in dev._ctrl.channels]
        assert dev.tx_enabled_channels == list(range(8))
        assert dev._tx_channel_names == expected_names
        assert dev.output_bits == [16] * 8
        assert [ch.name for ch in dev.channel] == expected_names
        assert all(
            getattr(dev, name) is dev.channel[i]
            for i, name in enumerate(expected_names)
        )


@pytest.mark.iio_hardware("ad5529r")
@pytest.mark.parametrize("device_class", ["ad552xr"])
def test_ad552xr_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)
    with adi.ad552xr(uri=iio_uri) as dev:
        expected_names = [ch.id for ch in dev._ctrl.channels]
        assert dev.tx_enabled_channels == list(range(16))
        assert dev._tx_channel_names == expected_names
        assert dev.output_bits == [16] * 16
        assert [ch.name for ch in dev.channel] == expected_names
        assert all(
            getattr(dev, name) is dev.channel[i]
            for i, name in enumerate(expected_names)
        )
