import pytest

# ADF4382 isn't in the adi_hardware_map.py in pylibiio
# This value will be changed to change to FMCOMMS11
hardware = ["adf4377"]
classname = "adi.adf4377"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [("volt0_output_power", 1, 11, 1, 0, 3), ("volt1_output_power", 1, 11, 1, 0, 3),],
)
def test_adf4377_attrs(
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
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value",
    [("volt0_en", 0), ("volt0_en", 1), ("volt1_en", 0), ("volt1_en", 1),],
)
def test_adf4377_attrs_bool(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


#########################################
@pytest.mark.no_os_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("reference_divider", 1, 63, 1, 0, 1),
        ("bleed_current", 0, 1023, 100, 0, 1),
        ("sysref_delay_adjust", 0, 127, 10, 0, 1),
    ],
)
def test_adf4377_attrs_no_os(
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
@pytest.mark.no_os_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("reference_doubler_enable", 0),
        ("reference_doubler_enable", 1),
        ("sysref_invert_adjust", 0),
        ("sysref_invert_adjust", 1),
        ("sysref_monitoring", 0),
        ("sysref_monitoring", 1),
    ],
)
def test_adf4382_attrs_bool_no_os(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)
