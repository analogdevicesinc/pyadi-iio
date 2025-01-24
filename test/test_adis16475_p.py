import pytest

import adi

hardware = "adis16475"
classname = "adi.adis16475"


@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_adis16475_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=16)


@pytest.mark.iio_hardware(hardware, True)
def test_adis16475_filter_low_pass_3db_frequency(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    for i in [10, 20, 40, 80, 164, 360, 720]:
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency == i

    for i in range(0, 10):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 10

    for i in range(11, 20):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 20

    for i in range(21, 40):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 40

    for i in range(41, 80):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 80

    for i in range(81, 164):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 164

    for i in range(165, 360):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 360

    for i in range(361, 720):
        adis16475.filter_low_pass_3db_frequency = i
        assert adis16475.filter_low_pass_3db_frequency <= 720


@pytest.mark.iio_hardware(hardware, True)
def test_adis16475_firmware_date(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    assert adis16475.firmware_date != "00-00-0000"


@pytest.mark.iio_hardware(hardware, True)
def test_adis16475_firmware_revision(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    assert adis16475.firmware_revision != "0.0"


@pytest.mark.iio_hardware(hardware, True)
def test_adis16475_product_id(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    assert adis16475.product_id != 0


@pytest.mark.iio_hardware(hardware, True)
def test_adis16475_serial_number(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    assert adis16475.serial_number != "0x0000"


@pytest.mark.iio_hardware(hardware, True)
def test_adis16476_conv_data(iio_uri):
    adis16475 = adi.adis16475(uri=iio_uri)

    assert adis16475.accel_x_conv != 0.0
    assert adis16475.accel_y_conv != 0.0
    assert adis16475.accel_z_conv != 0.0
    assert adis16475.anglvel_x_conv != 0.0
    assert adis16475.anglvel_y_conv != 0.0
    assert adis16475.anglvel_z_conv != 0.0
    assert adis16475.temp_conv != 0.0


@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("sample_rate", 1000, 2000, 1000, 0),
        ("anglvel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("anglvel_z_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_x_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_y_calibbias", -2147483648, 2147483647, 1, 0),
        ("accel_z_calibbias", -2147483648, 2147483647, 1, 0),
    ],
)
def test_adis16475_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)
