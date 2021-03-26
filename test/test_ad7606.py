import pytest

hardware = "ad7606b"
classname = "adi.ad7606"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, max_pow, tol", [("oversampling_ratio", 6, 0),],
)
def test_ad7606_attr(
    test_attribute_single_value_pow2, iio_uri, classname, attr, max_pow, tol
):
    test_attribute_single_value_pow2(iio_uri, classname, attr, max_pow, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_ad7606_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
