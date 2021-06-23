import pytest

hardware = "ad7799"
classname = "adi.ad7799"


#########################################
@pytest.mark.iio_hardware("ad7799")
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol", [("gain", 0, 7, 1, 0),],
)
def test_ad7799_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, step, stop, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(3))
def test_ad7799_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
