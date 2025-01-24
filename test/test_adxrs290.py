import pytest

hardware = "adxrs290"
classname = "adi.adxrs290"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("hpf_3db_frequency_available"), ("lpf_3db_frequency_available"),],
)
def test_adxrs290_attr_readonly(
    test_attribute_multiple_values_available_readonly, iio_uri, classname, attr
):
    test_attribute_multiple_values_available_readonly(iio_uri, classname, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("anglvel_x", "raw"),
        ("anglvel_y", "raw"),
        ("anglvel_x", "scale"),
        ("anglvel_y", "scale"),
    ],
)
def test_adxrs290_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, values, tol, repeats",
    [
        (
            "hpf_3db_frequency",
            [
                0.000000,
                0.01100,
                0.022000,
                0.044000,
                0.087000,
                0.175000,
                0.350000,
                0.700000,
                1.400000,
                2.800000,
                11.300000,
            ],
            0.5,
            2,
        ),
        (
            "lpf_3db_frequency",
            [
                480.000000,
                320.000000,
                160.000000,
                80.000000,
                56.600000,
                40.000000,
                28.300000,
                20.000000,
            ],
            0.5,
            2,
        ),
    ],
)
def test_adxrs290_attr(
    test_attribute_multiple_values, iio_uri, classname, attr, values, tol, repeats
):
    test_attribute_multiple_values(iio_uri, classname, attr, values, tol, repeats)
