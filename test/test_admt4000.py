import random

import iio
import pytest

import adi

hardware = ["admt4000"]
classname = "adi.admt4000"


def do_mock():
    def mock_set_trigger(self, value):
        pass

    # Mock the _set_trigger method in iio.Device
    iio.Device._set_trigger = mock_set_trigger


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, [0, 1, 2]])
def test_admt4000_rx_data(test_dma_rx, iio_uri, classname, channel):
    do_mock()
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("turns", "raw"),
        ("angle", "raw"),
        ("temp", "raw"),
        ("cosine", "raw"),
        ("sine", "raw"),
        ("radius", "raw"),
        ("turns", "scale"),
        ("angle", "scale"),
        ("temp", "scale"),
        ("radius", "scale"),
        ("temp", "offset"),
        ("turns", "processed"),
        ("angle", "processed"),
        ("temp", "processed"),
    ],
)
def test_admt4000_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    do_mock()
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_admt4000_attr_readonly_gpio(iio_uri, classname):
    do_mock()
    dev = eval(classname + "(uri='" + iio_uri + "')")
    assert len(dev.gpio) == 6
    for gpio in dev.gpio:
        assert gpio is not None


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("conversion_mode", "0.0"),
        ("conversion_mode", "1.0"),
        ("angle_filter_enable", "0.0"),
        ("angle_filter_enable", "1.0"),
    ],
)
def test_admt4000_attr_single_str(
    test_attribute_single_value_str, iio_uri, classname, attr, val
):
    do_mock()
    test_attribute_single_value_str(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("conv_sync_mode_available"), ("h8_corr_src_available"),],
)
def test_admt4000_attr_multiple_values_readonly(
    test_attribute_multiple_values_available_readonly, iio_uri, classname, attr
):
    test_attribute_multiple_values_available_readonly(iio_uri, classname, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "harmonics",
            [
                0.42305706499276774,
                157.40035229531108,
                0.3952010904372606,
                127.2546108682859,
                0.8250752450613099,
                124.40225451585263,
                0.8811647734156018,
                52.10340522521499,
            ],
        ),
        (
            "harmonics",
            [
                (0.6881799701516068, 7.6301230012092836),
                (0.5933649687824497, 356.95785043140296),
                (0.4485499122685841, 64.86013946791675),
                (0.23903747446272405, 320.40388424169925),
            ],
        ),
    ],
)
def test_admt4000_attr_harmonics(iio_uri, classname, attr, val):
    do_mock()
    dev = eval(classname + "(uri='" + iio_uri + "')")
    setattr(dev, attr, val)
    res = getattr(dev, attr)

    res = [item for tup in res for item in tup]
    if isinstance(val[0], tuple):
        val = [item for tup in val for item in tup]
    for i in range(len(val)):
        if i % 2 == 0:
            assert abs(val[i] - res[i]) < 0.1
        else:
            assert abs(val[i] - res[i]) < 60


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_admt4000_attr_faults(iio_uri, classname):
    do_mock()
    dev = eval(classname + "(uri='" + iio_uri + "')")
    res = getattr(dev, "faults")
    assert res is not None
