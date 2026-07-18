from unittest.mock import Mock, call

import pytest

import adi
from adi.device_base import rx_def

hardware = "ad6676"


@pytest.mark.iio_hardware(hardware)
def test_ad6676_common_parent_preserves_rx_contract(iio_uri):
    """AD6676 retains complex channel pairing and shared device identity."""
    with adi.ad6676(uri=iio_uri) as dev:
        assert "__init__" not in adi.ad6676.__dict__
        assert isinstance(dev, rx_def)
        assert dev._ctrl is dev._rxadc
        assert dev._rxadc.name == "axi-ad6676-hpc"
        assert dev._rx_channel_names == ["voltage0", "voltage1"]
        assert dev.rx_enabled_channels == [0]
        assert dev._num_rx_channels == 2
        assert dev.rx_buffer_size == 1024
        assert dev._complex_data is True


def test_ad6676_properties_preserve_attribute_forwarding():
    """Representative retained properties route through the legacy helpers."""
    dev = object.__new__(adi.ad6676)
    dev._rxadc = Mock()
    dev._get_iio_attr_str = Mock(return_value="value")
    dev._set_iio_attr = Mock()
    dev._get_iio_attr = Mock(return_value="ramp")

    assert dev.adc_frequency == "value"
    assert dev.bandwidth == "value"
    assert dev.sampling_frequency == "value"
    assert dev.test_mode == "ramp"

    dev.adc_frequency = 3_000_000_000
    dev.bandwidth = 100_000_000
    dev.sampling_frequency = 200_000_000
    dev.test_mode = "pn_long"

    assert dev._get_iio_attr_str.call_args_list == [
        call("voltage0", "adc_frequency", False),
        call("voltage0", "bandwidth", False),
        call("voltage0", "sampling_frequency", False),
    ]
    assert dev._set_iio_attr.call_args_list == [
        call("voltage0", "adc_frequency", False, 3_000_000_000),
        call("voltage0", "bandwidth", False, 100_000_000),
        call("voltage0", "sampling_frequency", False, 200_000_000),
        call("voltage0", "test_mode", False, "pn_long", dev._rxadc),
    ]
