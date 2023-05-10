import pytest

hardware = "lm75"
classname = "adi.lm75"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("max", -55000, 125000, 30000, 1, 10),
        ("max_hyst", -55000, 125000, 30000, 1, 10),
    ],
)
def test_lm75_attr(
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
