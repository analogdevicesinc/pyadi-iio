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
@pytest.mark.parametrize("param_set", [dict()])
def test_ad7405_rx_buffer(test_cyclic_buffer, iio_uri, classname, channel, param_set):
    test_cyclic_buffer(iio_uri, classname, channel, param_set)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, values", [("oversampling_ratio", [1, 32, 4096]),],
)
def test_ad7405_oversampling_ratio(
    test_attribute_multiple_values, iio_uri, classname, attr, values
):
    test_attribute_multiple_values(iio_uri, classname, attr, values, tol=0)
