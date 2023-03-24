import adi
import pytest

hardware = ["max9611"]
classname = "adi.max9611"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 1023, 1, 1, 3, "_channel_voltage_input"),
        ("raw", 0, 1023, 1, 1, 3, "_channel_temp"),
    ],
)
def test_max9611_raw_attr(
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
