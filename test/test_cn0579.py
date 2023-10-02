import pytest

hardware = "cn0579"
classname = "adi.cn0579"

#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_cn0579_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sampling_frequency",
            [
                1000,
                2000,
                4000,
                8000,
                16000,
                32000,
                64000,
                128000,
                256000,
                32000,
            ],  # End on a rate compatible with all power modes
        ),
        ("filter_type", ["WIDEBAND", "SINC5"],),
        ("power_mode", ["MEDIAN_MODE", "FAST_MODE"],),
        ("sync_start_enable", ["arm"],),
    ],
)
def test_cn0579_attr_multiple(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("CC_CH0", 0, 1, 1, 0),
        ("CC_CH1", 0, 1, 1, 0),
        ("CC_CH2", 0, 1, 1, 0),
        ("CC_CH3", 0, 1, 1, 0),
    ],
)
def test_cn0579_attr_single(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)
