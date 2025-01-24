import pytest

hardware = "ad7746"
classname = "adi.ad7746"
device_name = "ad7746"

VIN = "voltage0"
VIN_VDD = "voltage1"
TEMP_INT = "temp0"
TEMP_EXT = "temp1"
CIN1 = "capacitance0"
CIN1_DIFF = "capacitance0-capacitance2"
CIN2 = "capacitance1"
CIN2_DIFF = "capacitance1-capacitance3"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("device_name", [(device_name)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        (VIN, "raw"),
        (VIN_VDD, "raw"),
        (VIN, "scale"),
        (VIN_VDD, "scale"),
        (VIN, "sampling_frequency_available"),
        (VIN_VDD, "sampling_frequency_available"),
        (CIN1, "raw"),
        (CIN1_DIFF, "raw"),
        (CIN2, "raw"),
        (CIN2_DIFF, "raw"),
        (CIN1, "scale"),
        (CIN1_DIFF, "scale"),
        (CIN2, "scale"),
        (CIN2_DIFF, "scale"),
        (CIN1, "sampling_frequency_available"),
        (CIN1_DIFF, "sampling_frequency_available"),
        (CIN2, "sampling_frequency_available"),
        (CIN2_DIFF, "sampling_frequency_available"),
    ],
)
def test_ad7746_attr_readonly(
    test_attribute_single_value_device_name_channel_readonly,
    iio_uri,
    classname,
    device_name,
    channel,
    attr,
):
    test_attribute_single_value_device_name_channel_readonly(
        iio_uri, classname, device_name, channel, attr
    )


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("device_name", [(device_name)])
@pytest.mark.parametrize(
    "channel, attr, value",
    [
        (VIN, "calibscale_calibration", 1),
        (VIN_VDD, "calibscale_calibration", 1),
        (CIN1, "calibscale_calibration", 1),
        (CIN1_DIFF, "calibscale_calibration", 1),
        (CIN2, "calibscale_calibration", 1),
        (CIN2_DIFF, "calibscale_calibration", 1),
        (CIN1, "calibbias_calibration", 1),
        (CIN1_DIFF, "calibbias_calibration", 1),
        (CIN2, "calibbias_calibration", 1),
        (CIN2_DIFF, "calibbias_calibration", 1),
    ],
)
def test_ad7746_attr_write_only(
    test_attribute_write_only_str_device_channel,
    iio_uri,
    classname,
    device_name,
    channel,
    attr,
    value,
):
    test_attribute_write_only_str_device_channel(
        iio_uri, classname, device_name, channel, attr, value
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("device_name", [(device_name)])
@pytest.mark.parametrize(
    "channel, attr, start, stop, step, tol, repeats",
    [
        (CIN1, "calibscale", 1.0, 1.99999999, 0.1, 1.0, 2),
        (CIN1_DIFF, "calibscale", 1.0, 1.99999999, 0.1, 1.0, 2),
        (CIN2, "calibscale", 1.0, 1.99999999, 0.1, 1.0, 2),
        (CIN2_DIFF, "calibscale", 1.0, 1.99999999, 0.1, 1.0, 2),
    ],
)
def test_ad7746_attr_singleval(
    test_attribute_single_value_range_channel,
    iio_uri,
    classname,
    device_name,
    channel,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value_range_channel(
        iio_uri, classname, device_name, channel, attr, start, stop, step, tol, repeats
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("device_name", [(device_name)])
@pytest.mark.parametrize(
    "channel, attr, values, tol, repeats",
    [
        (VIN, "sampling_frequency", ["50", "31", "16", "8"], 0.5, 2),
        (VIN_VDD, "sampling_frequency", ["50", "31", "16", "8"], 0.5, 2),
        (
            CIN1,
            "sampling_frequency",
            ["91", "84", "50", "26", "16", "13", "11", "9"],
            0.5,
            2,
        ),
        (
            CIN1_DIFF,
            "sampling_frequency",
            ["91", "84", "50", "26", "16", "13", "11", "9"],
            0.5,
            2,
        ),
        (
            CIN2,
            "sampling_frequency",
            ["91", "84", "50", "26", "16", "13", "11", "9"],
            0.5,
            2,
        ),
        (
            CIN2_DIFF,
            "sampling_frequency",
            ["91", "84", "50", "26", "16", "13", "11", "9"],
            0.5,
            2,
        ),
        (CIN1, "calibbias", [0, 62745, 125, 50], 0.5, 2),
        (CIN1_DIFF, "calibbias", [0, 62745, 125, 50], 0.5, 2),
        (CIN2, "calibbias", [0, 62745, 125, 50], 0.5, 2),
        (CIN2_DIFF, "calibbias", [0, 62745, 125, 50], 0.5, 2),
        (CIN1, "offset", ["8127504"], 1, 2),
        (CIN2, "offset", ["8127504"], 1, 2),
        (CIN1, "offset", ["7111566"], 1, 2),
        (CIN2, "offset", ["7111566"], 1, 2),
        (CIN1, "offset", ["5079690"], 1, 2),
        (CIN2, "offset", ["5079690"], 1, 2),
    ],
)
def test_ad7746_attr_multiple_val(
    test_attribute_multiple_values_device_channel,
    iio_uri,
    classname,
    device_name,
    channel,
    attr,
    values,
    tol,
    repeats,
):
    test_attribute_multiple_values_device_channel(
        iio_uri, classname, device_name, channel, attr, values, tol, repeats
    )
