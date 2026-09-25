import pytest

import adi

hardware = ["ad7768-1", "adaq7767-1", "adaq7768-1", "adaq7769-1"]
classname = "adi.ad7768_1"
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
            ],  # End on a rate compatible with all power modes
        ),
        (
            "common_mode_voltage",
            ["(AVDD1-AVSS)/2", "2V5", "2V05", "1V9", "1V65", "1V1", "0V9", "OFF"],
        ),
    ],
)
def test_ad7768_1_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(common_mode_voltage="(AVDD1-AVSS)/2"),
        dict(common_mode_voltage="2V5"),
        dict(common_mode_voltage="2V05"),
        dict(common_mode_voltage="1V9"),
        dict(common_mode_voltage="1V65"),
        dict(common_mode_voltage="1V1"),
        dict(common_mode_voltage="0V9"),
        dict(common_mode_voltage="OFF"),
    ],
)
def test_ad7768_1_rx_data(test_dma_rx, iio_uri, classname, channel, param_set):
    test_dma_rx(iio_uri, classname, channel, param_set=param_set)
