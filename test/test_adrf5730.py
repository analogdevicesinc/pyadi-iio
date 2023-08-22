import pytest

hardware = "adrf5730"
classname = "adi.adrf5730"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, param_set", [("GPIO_attenuation", 0, 63, 1, 1, 10),]
)
def test_adrf5730_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    param_set,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, param_set
    )
