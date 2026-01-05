import pytest

hardware = ["adf41513"]
classname = "adi.adf41513"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [("frequency", 1600000000, 2400000000, 200000000, 0, 1)],
)
def test_adf41513_attrs(
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
@pytest.mark.parametrize("value", [0.001, 0.01, 0.1, 1.0, 10.0])
def test_adf41513_frequency_resolution(
    test_attribute_single_value_str, iio_uri, classname, value,
):
    test_attribute_single_value_str(
        iio_uri, classname, "frequency_resolution", value, 0
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value", [("powerdown", 1), ("powerdown", 0)],
)
def test_adf41513_attrs_bool(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value,
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)
