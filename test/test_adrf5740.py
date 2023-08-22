import pytest

hardware = "adrf5740"
classname = "adi.adrf5740"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, param_set", [("GPIO_attenuation", 0, 22, 2, 1, 10),]
)
def test_adrf5740_attr(
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
