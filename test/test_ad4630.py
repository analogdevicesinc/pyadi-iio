import pytest

hardware = ["ad4030-24", "ad4630-24"]
classname = "adi.ad4630"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad4630_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sample_rate",
            [10000, 50000, 100000, 200000, 500000, 1000000, 1750000, 2000000],
        ),
    ],
)
def test_ad4630_attr(test_attribute_multipe_values, iio_uri, classname, attr, val):
    test_attribute_multipe_values(iio_uri, classname, attr, val, 0)
