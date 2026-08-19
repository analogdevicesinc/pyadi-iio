import iio
import numpy as np
import pytest

import adi
from adi.device_base import rx_def

hardware = "adis16507-3"


@pytest.fixture
def trigger_calls(monkeypatch):
    """Record trigger assignments unsupported by iio-emu."""
    calls = []

    def record_trigger(device, trigger):
        calls.append((device, trigger))

    monkeypatch.setattr(iio.Device, "_set_trigger", record_trigger)
    return calls


@pytest.mark.iio_hardware(hardware)
def test_adis16507_common_parent_preserves_rx_and_trigger_state(iio_uri, trigger_calls):
    """The common RX parent retains the IMU's legacy construction contract."""
    with adi.adis16507(uri=iio_uri) as imu:
        assert isinstance(imu, rx_def)
        assert list(imu._rx_channel_names) == [
            "anglvel_x",
            "anglvel_y",
            "anglvel_z",
            "accel_x",
            "accel_y",
            "accel_z",
        ]
        assert imu.rx_enabled_channels == [0, 1, 2, 3, 4, 5]
        assert imu._num_rx_channels == 6
        assert imu.rx_buffer_size == 16
        assert imu._complex_data is False
        assert imu._rx_data_si_type is float
        assert imu._ctrl.name == "adis16507-3"
        assert imu._rxadc.name == "adis16507-3"
        assert imu._ctrl is not imu._rxadc
        assert imu._trigger.name == "adis16507-3-dev0"
        assert trigger_calls == [(imu._rxadc, imu._trigger)]


@pytest.mark.iio_hardware(hardware)
def test_adis16507_properties_forward_to_the_control_device(iio_uri, trigger_calls):
    """Device properties remain readable and writable after migration."""
    with adi.adis16507(uri=iio_uri) as imu:
        imu.sample_rate = 1000
        assert float(imu.sample_rate) == 1000

        imu.filter_low_pass_3db_frequency = 50
        assert float(imu.filter_low_pass_3db_frequency) == 50

        imu.current_timestamp_clock = "monotonic"
        assert imu._ctrl.attrs["current_timestamp_clock"].value == "monotonic"
        assert imu.current_timestamp_clock == []


@pytest.mark.iio_hardware(hardware)
def test_adis16507_rx_data(iio_uri, trigger_calls):
    """Each legacy IMU channel remains independently readable."""
    with adi.adis16507(uri=iio_uri) as imu:
        imu.rx_buffer_size = 8
        for channel in range(6):
            imu.rx_enabled_channels = [channel]
            data = imu.rx()
            assert isinstance(data, np.ndarray)
            assert data.shape == (8,)
            assert data.dtype == np.int32
            imu.rx_destroy_buffer()
