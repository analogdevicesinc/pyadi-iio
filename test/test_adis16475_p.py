import pytest

hardware = "adis16475"
classname = "adi.adis16475"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "classname, attr, start, stop, step, tol",
    [(classname, "sample_rate", 1000, 2000, 1000, 0)],
)
def test_adis16475_sample_rate(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)
