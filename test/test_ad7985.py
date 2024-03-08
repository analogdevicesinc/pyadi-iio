import pytest

hardware = "ad7985"
classname = "adi.ad7985"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sampling_frequency",
            [10000, 50000, 100000, 200000, 500000, 1000000, 2000000, 2500000],
        ),
    ],
)
def test_ad7985_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 1)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("classname", [classname])
def test_ad7985_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
