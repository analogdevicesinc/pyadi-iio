import pytest

hardware = "cn0511"
classname = "adi.CN0511"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, param_set",
    [
        ("frequency", 1, 2949120000, 1, 8, dict(sample_rate=5898240000)),
        ("raw", 1, 2 ** 15 - 1, 1, 8, None),
        ("sample_rate", 4915200000, 5775360000, 122880000, 8, None),
    ],
)
def test_cn0511_attr(
    test_attribute_single_value,
    classname,
    hardware,
    attr,
    start,
    stop,
    step,
    tol,
    param_set,
):
    test_attribute_single_value(
        classname, hardware, attr, start, stop, step, tol, param_set
    )


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("amp_enable", True),
        ("amp_enable", False),
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
