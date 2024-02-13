import pytest

hardware = ["ad7768"]
classname = "adi.ad7768"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sampling_frequency",
            [
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
        ("power_mode", ["LOW_POWER_MODE", "MEDIAN_MODE", "FAST_MODE"],),
    ],
)
def test_ad7768_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7])
@pytest.mark.parametrize(
    "param_set", [dict(filter_type="SINC5"), dict(filter_type="WIDEBAND")]
)
def test_ad7768_rx_data(test_dma_rx, iio_uri, classname, channel, param_set):
    test_dma_rx(iio_uri, classname, channel, param_set=param_set)
