import pytest

hardware = "ad7986"
classname = "adi.ad7986"


sampling_frequencies = range(50000, 2000000, 50000)
percent_tol = 2
repeats = 1
tols = [int(x * percent_tol / 100) for x in sampling_frequencies]
cases = [
    ("sampling_frequency", rate, rate + 1, 1, tol, repeats)
    for rate, tol in zip(sampling_frequencies, tols)
]
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats", cases,
)
def test_ad7986_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("classname", [classname])
def test_ad7986_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
