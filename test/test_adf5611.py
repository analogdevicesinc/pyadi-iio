import pytest

# This hardware is not yet supported for emulation
# Will run this by someone soon
hardware = ["adf5611"]
classname = "adi.adf5611"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [classname])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("altvolt0_rfout_power", 1, 3, 1, 0, 2),
        ("rfoutdiv_power", 1, 3, 1, 0, 2),
        ("reference_divider", 1, 16383, 2, 0, 1),
        ("rfout_frequency", 8000000000, 12000000000, 100000000, 0, 1),
    ],
)
def test_adf5611_attrs(
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
    "attr, value", [("en_rfoutdiv", 0), ("en_rfoutdiv", 1)],
)
def test_adf5611_attrs_bool(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)
