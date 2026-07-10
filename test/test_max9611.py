import pytest

import adi

hardware = ["max9611"]
classname = "adi.max9611"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, lower, upper, repeats, sub_channel",
    [("raw", 0, 1023, 3, "voltage1"), ("raw", 0, 1023, 3, "temp"),],
)
def test_max9611_raw_attr(
    test_attribute_single_value_readonly,
    iio_uri,
    classname,
    attr,
    lower,
    upper,
    repeats,
    sub_channel,
):
    test_attribute_single_value_readonly(
        iio_uri, classname, attr, lower, upper, repeats, sub_channel
    )
