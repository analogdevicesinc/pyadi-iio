import pytest

hardware = "packrf"
classname = "adi.adis16460"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "classname, attr, max_pow, tol", [(classname, "sample_rate", 12, 0)],
)
def test_adis16460_sample_rate(
    test_attribute_single_value_pow2, iio_uri, classname, attr, max_pow, tol
):
    test_attribute_single_value_pow2(iio_uri, classname, attr, max_pow, tol)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5])
def test_adis16460_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
