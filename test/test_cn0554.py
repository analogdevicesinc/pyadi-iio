import pytest

hardware = "cn0554"
classname = "adi.cn0554"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, param_set",
    [
        ("sample_rate", 10, 19200, 10, 10, 4),
        ("rx_enabled_channels", 0, 7, 1, 1, 8),
        ("in_scale", 11, 40, 1, 1, 3),
    ],
)
def test_cn0554_attr(
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


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, max_pow, tol", [("rx_buffer_size", 12, 10),],
)
def test_cn0554_attr_pow2(
    test_attribute_single_value_pow2, iio_uri, classname, attr, max_pow, tol
):
    test_attribute_single_value_pow2(iio_uri, classname, attr, max_pow, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value, tol",
    [
        ("rx_output_type", "SI", 1),
        ("rx_output_type", "raw", 1),
        ("voltage01_in_range", "+/-13.75", 1),
        ("voltage01_in_range", "+27.5", 1),
        ("voltage01_in_range", "+2.5", 1),
        ("voltage23_in_range", "+/-13.75", 1),
        ("voltage23_in_range", "+27.5", 1),
        ("voltage23_in_range", "+2.5", 1),
        ("voltage45_in_range", "+/-13.75", 1),
        ("voltage45_in_range", "+27.5", 1),
        ("voltage45_in_range", "+2.5", 1),
        ("voltage67_in_range", "+/-13.75", 1),
        ("voltage67_in_range", "+27.5", 1),
        ("voltage67_in_range", "+2.5", 1),
        ("voltage89_in_range", "+/-13.75", 1),
        ("voltage89_in_range", "+27.5", 1),
        ("voltage89_in_range", "+2.5", 1),
        ("voltage1011_in_range", "+/-13.75", 1),
        ("voltage1011_in_range", "+27.5", 1),
        ("voltage1011_in_range", "+2.5", 1),
        ("voltage1213_in_range", "+/-13.75", 1),
        ("voltage1213_in_range", "+27.5", 1),
        ("voltage1213_in_range", "+2.5", 1),
        ("voltage1415_in_range", "+/-13.75", 1),
        ("voltage1415_in_range", "+27.5", 1),
        ("voltage1415_in_range", "+2.5", 1),
    ],
)
def test_cn0554_attr_string(
    test_attribute_single_value_str, iio_uri, classname, attr, value, tol
):
    test_attribute_single_value_str(iio_uri, classname, attr, value, tol)
