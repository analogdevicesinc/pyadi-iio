import adi
import pytest

hardware = ["ADXL312", "ADXL313", "ADXL314"]
classname = "adi.adxl313"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2])
def test_adxl313_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("calibbias", 0, 6, 1, 1, 3, "accel_x"),
        ("calibbias", 0, 6, 1, 1, 3, "accel_y"),
        ("calibbias", 0, 6, 1, 1, 3, "accel_z"),
    ],
)
def test_adxl313_calibbias_attr(
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
    # Get device name
    sdr = eval(classname + "(uri='" + iio_uri + "')")

    # Set test parameters depending on device name
    if sdr._device_name == "ADXL312":
        scale_factor = 11600
    elif sdr._device_name == "ADXL313":
        scale_factor = 3900
    elif sdr._device_name == "ADXL314":
        scale_factor = 195000

    stop = stop * scale_factor
    step = step * scale_factor

    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("sampling_frequency", 25, 50, 25, 1, 3, "accel_x"),
        ("sampling_frequency", 50, 100, 50, 1, 3, "accel_y"),
        ("sampling_frequency", 100, 200, 100, 1, 3, "accel_z"),
    ],
)
def test_adxl313_sample_freuency_attr(
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


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("range", 0.5, 1.0, 0.5, 1, 3, "accel_x"),
        ("range", 1.0, 2.0, 1.0, 1, 3, "accel_y"),
        ("range", 2.0, 4.0, 2.0, 1, 3, "accel_z"),
    ],
)
def test_adxl313_range_attr(
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
    # Get device name.
    sdr = eval(classname + "(uri='" + iio_uri + "')")

    #  Set test parameters depending on device name
    scale_factor = 1
    if sdr._device_name == "ADXL312":
        scale_factor = 3
    elif sdr._device_name == "ADXL314":
        pytest.skip("Test not applicable to ADXL314. Range is fixed.")

    start = start * scale_factor
    stop = stop * scale_factor
    step = step * scale_factor

    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [("scale", 0.009576806, 0.076614453, 0.067037647, 1, 3, "accel_x"),],
)
def test_adxl313_scale_attr(
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
    # Get device name
    sdr = eval(classname + "(uri='" + iio_uri + "')")

    # Set test parameters depending on device name
    if sdr._device_name == "ADXL312":
        setattr(getattr(sdr, "accel_x"), attr, 12.0)
        start = 0.028439285
        stop = 0.22751428
        step = 0.199074995
    elif sdr._device_name == "ADXL313":
        setattr(getattr(sdr, "accel_x"), attr, 4.0)
    elif sdr._device_name == "ADXL314":
        pytest.skip("Test not applicable to ADXL314. Scale is fixed.")

    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )
