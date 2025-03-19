import pytest

# ADF4382 isn't in the adi_hardware_map.py in pylibiio
# This value will be changed to change to FMCOMMS11
hardware = ["adf4382"]
classname = "adi.adf4382"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("altvolt0_output_power", 1, 11, 1, 0, 5),
        ("altvolt1_output_power", 1, 11, 1, 0, 5),
    ],
)
def test_adf4382_attrs(
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
    [("altvolt0_en", 0), ("altvolt0_en", 1), ("altvolt1_en", 0), ("altvolt1_en", 1),],
)
def test_adf4382_attrs_bool(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


#########################################
@pytest.mark.no_os_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [("reference_divider", 1, 63, 1, 0, 1), ("bleed_current", 0, 8191, 100, 0, 1),],
)
def test_adf4382_attrs_no_os(
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
        ("reference_doubler_en", 0),
        ("reference_doubler_en", 1),
        ("sw_sync_en", 0),
        ("sw_sync_en", 1),
    ],
)
def test_adf4382_attrs_bool_no_os(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)
