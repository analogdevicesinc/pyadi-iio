import pytest

hardware = ["cn0565"]
classname = "adi.cn0565"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("electrode_count", 0, 64, 8, 1, 1),
        ("force_distance", 0, 8, 1, 0, 0),
        ("sense_distance", 0, 8, 1, 0, 0),
    ],
)
def test_cn0565_attrs(
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
