import pytest

hardware = ["adt7420"]
classname = "adi.adt7420"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("temp_max", 5, 50, 5, 1, 2, "_channel"),
        ("temp_min", 0, 40, 5, 1, 1, "_channel"),
        ("temp_crit", 80, 150, 5, 10, 1, "_channel"),
        ("temp_hyst", 5, 20, 1, 1, 1, "_channel"),
    ],
)
def test_adt7420_attrs(
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
