import random
from test.attr_tests import floor_step_size

import pytest

import adi
from adi.cn0540 import cn0540
from adi.device_base import rx_def

hardware = "cn0540"
classname = "adi.cn0540.cn0540"


@pytest.mark.iio_hardware(hardware)
def test_cn0540_common_parent_preserves_composite_state(iio_uri):
    """Common RX setup retains all four board-device references."""
    with cn0540(uri=iio_uri) as device:
        assert "__init__" not in cn0540.__dict__
        assert isinstance(device, rx_def)
        assert device._ctrl.name == "ad7768-1"
        assert device._rxadc.name == "ad7768-1"
        assert device._ctrl is not device._rxadc
        assert device._ltc2606.name == "ltc2606"
        assert device._gpio.name == "one-bit-adc-dac"
        assert device._ltc2308.name == "ltc2308"
        assert device._rx_channel_names == ["voltage0"]
        assert device.rx_enabled_channels == [0]
        assert device._num_rx_channels == 1
        assert device.rx_buffer_size == 1024
        assert device._complex_data is False
        assert device._rx_data_si_type is float


@pytest.mark.iio_hardware(hardware)
def test_cn0532_inherits_cn0540_common_initialization(iio_uri):
    """CN0532 keeps its board state without a forwarding constructor."""
    with adi.cn0532(uri=iio_uri) as device:
        assert "__init__" not in adi.cn0532.__dict__
        assert isinstance(device, cn0540)
        assert device._ctrl.name == "ad7768-1"
        assert device._rxadc.name == "ad7768-1"
        assert device._ltc2606.name == "ltc2606"
        assert device._gpio.name == "one-bit-adc-dac"
        assert device._ltc2308.name == "ltc2308"
        assert device.rx_enabled_channels == [0]


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_cn0540_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [("sample_rate", [256000, 128000, 64000, 32000, 16000, 8000, 4000, 2000, 1000,],),],
)
def test_cn0540_attr_multiple(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("monitor_powerup", 0),
        ("monitor_powerup", 1),
        ("fda_disable_status", 0),
        ("fda_disable_status", 1),
        ("red_led_enable", 0),
        ("red_led_enable", 1),
        ("sw_cc", 0),
        ("sw_cc", 1),
        ("fda_mode", "low-power"),
        ("fda_mode", "full-power"),
    ],
)
def test_cn0540_attr_boolean(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("sw_ff_status"),],
)
def test_cn0540_attr_boolean_readonly(
    test_attribute_single_value_boolean_readonly, iio_uri, classname, attr
):
    test_attribute_single_value_boolean_readonly(iio_uri, classname, attr)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, repeats ", [("shift_voltage", 0, 65535, 1, 2),],
)
def test_cn0540_shift_voltage(iio_uri, classname, attr, start, stop, step, repeats):
    device = cn0540(uri=iio_uri)
    bi = eval(classname + "(uri='" + iio_uri + "')")

    if not hasattr(bi, attr):
        raise AttributeError(f"no attribute named: {attr}")

    # Pick random number in operational range
    numints = int((stop - start) / step)
    for _ in range(repeats):
        ind = random.randint(0, numints)
        val = start + step * ind
        if isinstance(val, float):
            val = floor_step_size(val, str(step))

        setattr(bi, "raw", val)
        assert 0 <= device.shift_voltage <= 4997.04375


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_cn0540_readonly(iio_uri):
    device = cn0540(uri=iio_uri)
    attr = [device.input_voltage, device.sensor_voltage]
    for attr_name in attr:
        assert type(attr_name) != None
