import pytest

hardware = "ad4001"
classname = "adi.ad4001"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val, tol, repeats, sleep, sub_channel",
    [
        (
            "sampling_frequency",
            [10000, 50000, 100000, 200000, 500000, 1000000, 2000000],
            1,
            1,
            0,
            "_channel",
        ),
    ],
)
def test_ad4001_attr(
    test_attribute_multiple_values,
    iio_uri,
    classname,
    attr,
    val,
    tol,
    repeats,
    sleep,
    sub_channel,
):
    test_attribute_multiple_values(
        iio_uri, classname, attr, val, 1, repeats, sleep, sub_channel
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad4001_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 15)
