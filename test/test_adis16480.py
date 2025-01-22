import pytest

import adi

hardware = "adis16480"
classname = "adi.adis16480"
device_name = "adis16480"

########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_adis16480_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=16)


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_adis16480_conv_data(iio_uri):
    adis16480 = adi.adis16480(uri=iio_uri)

    assert adis16480.accel_x_conv != 0.0
    assert adis16480.accel_y_conv != 0.0
    assert adis16480.accel_z_conv != 0.0
    assert adis16480.anglvel_x_conv != 0.0
    assert adis16480.anglvel_y_conv != 0.0
    assert adis16480.anglvel_z_conv != 0.0
    assert adis16480.temp_conv != 0.0


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
        ("magn_x_calibbias", -32134, 32134, 1, 0),
        ("magn_y_calibbias", -32134, 32134, 1, 0),
        ("magn_z_calibbias", -32134, 32134, 1, 0),
        ("pressure_calibbias", -32134, 32134, 1, 0),
        ("anglvel_x_calibscale", -32134, 32134, 1, 0),
        ("anglvel_y_calibscale", -32134, 32134, 1, 0),
        ("anglvel_z_calibscale", -32134, 32134, 1, 0),
        ("accel_x_calibscale", -32134, 32134, 1, 0),
        ("accel_y_calibscale", -32134, 32134, 1, 0),
        ("accel_z_calibscale", -32134, 32134, 1, 0),
    ],
)
def test_adis16480_attr(
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
        ("magn_x_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("magn_y_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
        ("magn_z_filter_low_pass_3db_frequency", [0, 55, 275, 310], 0.5, 2),
    ],
)
def test_adis16480_attr_multiple_val(
    test_attribute_multiple_values, iio_uri, classname, attr, values, tol, repeats,
):
    test_attribute_multiple_values(iio_uri, classname, attr, values, tol, repeats)


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_adis16480_firmware_date(iio_uri):
    adis16480 = adi.adis16480(uri=iio_uri)

    assert adis16480.firmware_date != "00-00-0000"


@pytest.mark.iio_hardware(hardware, True)
def test_adis16480_firmware_revision(iio_uri):
    adis16480 = adi.adis16480(uri=iio_uri)

    assert adis16480.firmware_revision != "0.0"


@pytest.mark.iio_hardware(hardware, True)
def test_adis16480_product_id(iio_uri):
    adis16480 = adi.adis16480(uri=iio_uri)

    assert adis16480.product_id != 0


@pytest.mark.iio_hardware(hardware, True)
def test_adis16480_serial_number(iio_uri):
    adis16480 = adi.adis16480(uri=iio_uri)

    assert adis16480.serial_number != "0x0000"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "classname",
    [
        "adi.adis16375",
        "adi.adis16480",
        "adi.adis16485",
        "adi.adis16488",
        "adi.adis16490",
        "adi.adis16495",
        "adi.adis16497",
        "adi.adis16545",
        "adi.adis16547",
    ],
)
def test_adis16XXX_create(iio_uri, classname):
    # This test is a little hack to just enumerate all the classes even though
    # we don't have the exact hardware
    emulation_hw = "adis16480"
    imu = eval(classname)
    imu.compatible_parts = [emulation_hw]
    imu.disable_trigger = True

    # Try to create the object
    imu = imu(uri=iio_uri)
