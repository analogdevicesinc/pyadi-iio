import pytest

import adi

hardware = ["ad5940"]
classname = "adi.ad5940"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("excitation_frequency", 0, 250000, 10000, 1, 1),
        ("excitation_amplitude", 0, 800, 100, 1, 1),
        ("impedance_mode", 0, 1, 1, 1, 1),
        ("magnitude_mode", 0, 1, 1, 1, 1),
    ],
)
def test_ad5940_attrs(
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
