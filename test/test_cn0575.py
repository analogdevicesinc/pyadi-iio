import pytest

hardware = "cn0575"
classname = "adi.cn0575"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("max", -55000, 125000, 30000, 1, 10, "adt75"),
        ("max_hyst", -55000, 125000, 30000, 1, 10, "adt75"),
    ],
)
def test_adt75_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val", [("led", [1, 0],),],
)
def test_led_attr(test_attribute_multipe_values, iio_uri, classname, attr, val):
    test_attribute_multipe_values(iio_uri, classname, attr, val, 0, repeats=10)
