import pytest

# ADF4355 isn't in the adi_hardware_map.py in pylibiio
# This value will be changed to change to FMCOMMS11
hardware = ["adf4355"]
classname = "adi.adf4355"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("frequency_altvolt0", 0, 6800000000, 1000000, 1000, 1),
        ("frequency_altvolt1", 0, 6800000000, 1000000, 1000, 1),
        ("powerdown_altvolt0", 0, 1, 1, 1, 1),
        ("powerdown_altvolt1", 0, 1, 1, 1, 1),
    ],
)
def test_adf4355_attrs(
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
