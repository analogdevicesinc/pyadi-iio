import pytest

hardware = "AD5144"
classname = "adi.ad514x"

#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [("nvm_programming", ["disable", "enable"]), ("rdac_wp", ["enable", "disable"]),],
)
def test_ad514x_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 1)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "subchannel", ["resistance0", "resistance1", "resistance2", "resistance3"]
)
@pytest.mark.parametrize(
    "attr, val",
    [
        ("bottom_scale_option", ["enter", "exit"]),
        ("top_scale_option", ["enter", "exit"]),
        ("shutdown", ["enable", "disable"]),
        ("rdac_6db", ["increment", "decrement"]),
        ("rdac_linear", ["increment", "decrement"]),
    ],
)
def test_ad514x_channel_attr(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)
