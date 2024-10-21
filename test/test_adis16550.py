import adi
import pytest

hardware = "adis16550"
classname = "adi.adis16550"
device_name = "adis16550"


########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_adis16550_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=16)


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_adis16550_conv_data(iio_uri):
    adis16550 = adi.adis16550(uri=iio_uri)

    assert adis16550.accel_x_conv != 0.0
    assert adis16550.accel_y_conv != 0.0
    assert adis16550.accel_z_conv != 0.0
    assert adis16550.anglvel_x_conv != 0.0
    assert adis16550.anglvel_y_conv != 0.0
    assert adis16550.anglvel_z_conv != 0.0
    assert adis16550.temp_conv != 0.0


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("anglvel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_x_calibscale", -32134, 32134, 1, 0),
        ("anglvel_y_calibscale", -32134, 32134, 1, 0),
        ("anglvel_z_calibscale", -32134, 32134, 1, 0),
        ("accel_x_calibscale", -32134, 32134, 1, 0),
        ("accel_y_calibscale", -32134, 32134, 1, 0),
        ("accel_z_calibscale", -32134, 32134, 1, 0),
    ],
)
def test_adis16550_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, values, tol, repeats",
    [
        ("sample_rate", [5, 10, 246, 1230, 2460], 0.5, 2),
        ("anglvel_x_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("anglvel_y_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("anglvel_z_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_x_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_y_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("accel_z_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
    ],
)
def test_adis16550_attr_multiple_val(
    test_attribute_multiple_values, iio_uri, classname, attr, values, tol, repeats,
):
    test_attribute_multiple_values(iio_uri, classname, attr, values, tol, repeats)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "classname", ["adis16550", "adis16550w",],
)
def test_adis16XXX_create(iio_uri, classname):
    # This test is a little hack to just enumerate all the classes even though
    # we don't have the exact hardware
    emulation_hw = "adis16550"
    imu = eval(classname)
    imu.compatible_parts = [emulation_hw]
    imu.disable_trigger = True

    # Try to create the object
    imu = imu(uri=iio_uri)
