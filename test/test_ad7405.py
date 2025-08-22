import pytest

hardware = ["ad7405", "adum7701", "adum7702", "adum7703"]
classname = "adi.ad7405"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad7405_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad7405_rx_buffer(test_cyclic_buffer, iio_uri, classname, channel):
    test_cyclic_buffer(iio_uri, classname, channel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_ad7405_oversampling_ratio(test_attribute_single_value, iio_uri, classname):
    test_attribute_single_value(iio_uri, classname, "oversampling_ratio")
