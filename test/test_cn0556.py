import pytest

import adi

hardware = "cn0556"
classname = "adi.cn0556"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("drxn", 0, 1, 1, 1),
        ("enable", 0, 1, 1, 1),
        ("buck_target_output_voltage", 2, 14, 1, 1),
        ("buck_input_undervoltage", 12, 54, 1, 1),
        ("buck_input_current_limit", 0.07, 10, 1, 0.01),
        ("buck_output_current_limit", 0, 35, 1, 0.01),
        ("boost_target_output_voltage", 14, 56, 1, 1),
        ("boost_input_undervoltage", 12, 54, 1, 1),
        ("boost_input_current_limit", 0, 35, 1, 0.01),
        ("boost_output_current_limit", 1, 10, 1, 0.01),
        ("report", 0, 1, 1, 1),
        ("fault", 0, 1, 1, 1),
        ("intvcc_voltage", 0, 4, 1, 0.01),
        ("share_voltage", 0, 4, 1, 0.01),
        ("buck_input_voltage", 14, 56, 1, 0.01),
        ("buck_output_voltage", 2, 14, 1, 0.01),
        ("buck_input_current", 1, 10, 1, 0.01),
        ("buck_output_current", 1, 35, 1, 0.01),
        ("boost_input_voltage", 8, 14, 1, 0.01),
        ("boost_output_voltage", 14, 56, 1, 0.01),
        ("boost_input_current", 0, 35, 1, 0.01),
        ("boost_output_current", 1, 10, 1, 0.01),
    ],
)
def test_cn0556_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol,
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)
