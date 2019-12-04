import pytest

hardware = "packrf"
classname = "adi.adis16460"


@pytest.mark.parametrize(
    "classname, hardware, attr, max_pow, tol",
    [(classname, hardware, "sample_rate", 12, 0)],
)
def test_adis16460_sample_rate(
    test_attribute_single_value_pow2, classname, hardware, attr, max_pow, tol
):
    test_attribute_single_value_pow2(classname, hardware, attr, max_pow, tol)


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5])
def test_adis16460_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)
