import pytest

hardware = ["ad7768"]
classname = "adi.ad7768"

#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7])
def test_ad7768_rx_data(test_dma_rx, iio_uri, classname, channel):
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
    ],
)
def test_ad4630_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)
