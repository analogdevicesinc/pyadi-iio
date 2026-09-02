import iio
import numpy as np
import pytest

import adi
from adi.device_base import rx_def

hardware = "adis16550"
classname = "adi.adis16550"
device_name = "adis16550"


def do_mock():
    def mock_set_trigger(self, value):
        pass

    # Mock the _set_trigger method in iio.Device
    iio.Device._set_trigger = mock_set_trigger


#########################################
@pytest.mark.iio_hardware(hardware, False)
def test_adis16550_conv_data(iio_uri):
    do_mock()
    adis16550 = adi.adis16550(uri=iio_uri)

    assert adis16550.accel_x_conv != 0.0
    assert adis16550.accel_y_conv != 0.0
    assert adis16550.accel_z_conv != 0.0
    assert adis16550.anglvel_x_conv != 0.0
    assert adis16550.anglvel_y_conv != 0.0
    assert adis16550.anglvel_z_conv != 0.0
    assert adis16550.temp_conv != 0.0


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("anglvel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_x_calibscale", 0, 65535, 1, 0),
        ("anglvel_y_calibscale", 0, 65535, 1, 0),
        ("anglvel_z_calibscale", 0, 65535, 1, 0),
        ("accel_x_calibscale", 0, 65535, 1, 0),
        ("accel_y_calibscale", 0, 65535, 1, 0),
        ("accel_z_calibscale", 0, 65535, 1, 0),
    ],
)
def test_adis16550_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    do_mock()
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, values, tol, repeats",
    [
        ("sample_rate", [5, 10, 246, 1230, 2460], 0.5, 2),
        ("anglvel_x_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("anglvel_y_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("anglvel_z_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_x_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_y_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_z_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
    ],
)
def test_adis16550_attr_multiple_val(
    test_attribute_multiple_values, iio_uri, classname, attr, values, tol, repeats,
):
    do_mock()
    test_attribute_multiple_values(iio_uri, classname, attr, values, tol, repeats)


@pytest.mark.iio_hardware(hardware)
def test_adis16550_common_parent_preserves_structure(iio_uri, monkeypatch):
    """The shared RX parent retains device, channel, and trigger state."""
    trigger_calls = []

    def record_trigger(device, trigger):
        trigger_calls.append((device, trigger))

    monkeypatch.setattr(iio.Device, "_set_trigger", record_trigger)

    with adi.adis16550(uri=iio_uri) as imu:
        assert isinstance(imu, rx_def)
        assert imu._rx_channel_names == [
            "anglvel_x",
            "anglvel_y",
            "anglvel_z",
            "accel_x",
            "accel_y",
            "accel_z",
            "temp0",
            "deltaangl_x",
            "deltaangl_y",
            "deltaangl_z",
            "deltavelocity_x",
            "deltavelocity_y",
            "deltavelocity_z",
        ]
        assert imu.rx_enabled_channels == list(range(13))
        assert imu.rx_buffer_size == 16
        assert imu._ctrl.name == "adis16550"
        assert imu._rxadc.name == "adis16550"
        assert imu._ctrl is not imu._rxadc
        assert imu._trigger.name == "adis16550-dev0"
        assert trigger_calls == [(imu._rxadc, imu._trigger)]

        expected_wrappers = {
            "anglvel_x": adi.adis16550._anglvel_accel_channels,
            "accel_z": adi.adis16550._anglvel_accel_channels,
            "temp": adi.adis16550._temp_channel,
            "deltaangl_y": adi.adis16550._delta_channels,
            "deltavelocity_z": adi.adis16550._delta_channels,
        }
        for name, wrapper_type in expected_wrappers.items():
            wrapper = getattr(imu, name)
            assert isinstance(wrapper, wrapper_type)
            assert wrapper._ctrl is imu._ctrl


@pytest.mark.iio_hardware(hardware)
def test_adis16550_custom_constructor_and_disabled_trigger(iio_uri, monkeypatch):
    """Custom device selection and trigger disabling remain supported."""
    trigger_calls = []
    monkeypatch.setattr(
        iio.Device,
        "_set_trigger",
        lambda device, trigger: trigger_calls.append((device, trigger)),
    )
    monkeypatch.setattr(adi.adis16550, "disable_trigger", True)

    with adi.adis16550(
        uri=iio_uri, device_name="adis16550", trigger_name="custom-trigger"
    ) as imu:
        assert imu._control_device_name == "adis16550"
        assert imu._rx_data_device_name == "adis16550"
        assert imu._trigger_name == "custom-trigger"
        assert not hasattr(imu, "_trigger")
        assert trigger_calls == []

    with pytest.raises(Exception, match="Not a compatible device"):
        adi.adis16550(uri=iio_uri, device_name="not-adis16550")


@pytest.mark.iio_hardware(hardware)
def test_adis16550_buffered_read_preserves_all_data_channels(iio_uri, monkeypatch):
    """Buffered reads continue to return all 13 configured data channels."""
    monkeypatch.setattr(iio.Device, "_set_trigger", lambda device, trigger: None)

    with adi.adis16550(uri=iio_uri) as imu:
        imu.rx_buffer_size = 8
        data = imu.rx()
        assert isinstance(data, list)
        assert len(data) == 13
        assert all(isinstance(channel, np.ndarray) for channel in data)
        assert all(channel.shape == (8,) for channel in data)
