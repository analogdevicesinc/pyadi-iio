import pytest

hardware = "cn0511"
classname = "adi.CN0511"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("raw", 1, 2 ** 15 - 1, 1, 8),
        ("sample_rate", 4915200000, 5898240000, 122880000, 8),
    ],
)
def test_cn0511_attr(
    test_attribute_single_value, classname, hardware, attr, start, stop, step, tol
):
    test_attribute_single_value(classname, hardware, attr, start, stop, step, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("amp_enable", True),
        ("amp_enable", False),
        ("temperature_enable", False),
        ("temperature_enable", True),
        ("FIR85_enable", True),
        ("FIR85_enable", False),
        ("tx_enable", False),
        ("tx_enable", True),
    ],
)
def test_cn0511_attr_boolean(
    test_attribute_single_value_boolean, classname, hardware, attr, value
):
    test_attribute_single_value_boolean(classname, hardware, attr, value)
