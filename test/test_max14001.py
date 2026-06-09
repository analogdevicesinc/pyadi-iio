import pytest

hardware = "max14001"
classname = "adi.max14001"


######################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, lower, upper, repeats, sub_channel", [("raw", 0, 1023, 2, "voltage"),],
)
def test_max14001_attr(
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
