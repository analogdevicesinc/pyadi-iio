import pytest

hardware = "ad3530r"
classname = "adi.ad353xr"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 20000, 2000, 1, 3, "voltage0"),
        ("raw", 0, 20000, 2000, 1, 3, "voltage1"),
    ],
)
def test_ad353xr_raw_attr(
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
    "attr, val",
    [
        ("reference_select", ["external_ref", "internal_ref"],),
        ("range", ["0_to_VREF", "0_to_2VREF"],),
    ],
)
def test_ad353xr_global_attr(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", ["voltage0", "voltage1", "voltage2", "voltage3"])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "operating_mode",
            ["normal_operation", "1kOhm_to_gnd", "7k7Ohm_to_gnd", "32kOhm_to_gnd"],
        ),
    ],
)
def test_ad353xr_channel_attr(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)
