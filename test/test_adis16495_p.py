import pytest

hardware = "rpi"
classname = "adi.adis16495"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "classname, attr, max_pow, tol", [(classname, "sample_rate", 11, 0)],
)
def test_adis16495_sample_rate(
    test_attribute_single_value_pow2, iio_uri, classname, attr, max_pow, tol
):
    test_attribute_single_value_pow2(iio_uri, classname, attr, max_pow, tol)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("anglvel_x_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("anglvel_y_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("anglvel_z_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("accel_x_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("accel_y_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("accel_z_filter_low_pass_3db_frequency", 0, 300, 1, 200),
        ("anglvel_x_calibscale", -32768, 32768, 1, 0),
        ("anglvel_y_calibscale", -32768, 32768, 1, 0),
        ("anglvel_z_calibscale", -32768, 32768, 1, 0),
        ("accel_x_calibscale", -32768, 32768, 1, 0),
        ("accel_y_calibscale", -32768, 32768, 1, 0),
        ("accel_z_calibscale", -32768, 32768, 1, 0),
        ("anglvel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_z_calibbias", -2147483648, 2147483647, 1, 0),
    ],
)
def test_adis16495_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


@pytest.mark.skip(reason="Test is currently failing...")
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5])
def test_adis16495_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
