import pytest

hardware = "adxl380"
classname = "adi.adxl380"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2])
def test_adxl380_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("calibbias", 0, 30000, 10000, 1, 3, "accel_x"),
        ("calibbias", 0, 30000, 10000, 1, 3, "accel_y"),
        ("calibbias", 0, 30000, 10000, 1, 3, "accel_z"),
        ("filter_high_pass_3db_frequency", 39.520000, 39.520000, 1, 1, 3, "accel_x"),
        ("filter_high_pass_3db_frequency", 39.520000, 39.520000, 1, 1, 3, "accel_y"),
        ("filter_high_pass_3db_frequency", 39.520000, 39.520000, 1, 1, 3, "accel_z"),
        ("filter_low_pass_3db_frequency", 4000, 4000, 1, 1, 3, "accel_x"),
        ("filter_low_pass_3db_frequency", 4000, 4000, 1, 1, 3, "accel_y"),
        ("filter_low_pass_3db_frequency", 4000, 4000, 1, 1, 3, "accel_z"),
    ],
)
def test_adxl380_attr(
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
