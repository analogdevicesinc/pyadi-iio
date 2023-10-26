import pytest

hardware = "ad2s1210"
classname = "adi.ad2s1210"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [classname])
@pytest.mark.parametrize("channel", ["angl0", "anglvel0", ["angl0", "anglvel0"]])
def test_ad2s1210_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=1024)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [classname])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [("excitation_frequency", 2000, 20000, 250, 1, 10),],
)
def test_ad2s1210_attr(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [classname])
@pytest.mark.parametrize(
    "attr, value", [("hysteresis_enable", True), ("hysteresis_enable", False),],
)
def test_ad2s1210_attr_boolean(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)
