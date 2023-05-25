import pytest

hardware = "adxl355"
classname = "adi.adxl355"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2])
def test_adxl355_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("calibbias", -30000, 30000, 10000, 1, 3, "accel_x"),
        ("calibbias", -30000, 30000, 10000, 1, 3, "accel_y"),
        ("calibbias", -30000, 30000, 10000, 1, 3, "accel_z"),
    ],
)
def test_adxl355_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )
