import iio
import pytest

hardware = ["tmc5240", "admt4000ard1z"]
classname = "adi.tmc5240"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 2000000, 2000000, 50000, 1, 2, "angular_position"),
        ("raw", 1000000, 2000000, 50000, 1, 2, "angular_velocity"),
        ("raw", -2000000, -1000000, 50000, 1, 2, "angular_velocity"),
    ],
)
def test_tmc5240_ch_attr(
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
    "attr, start, stop, step, tol, repeats",
    [
        ("amax", 1000000, 2000000, 50000, 1, 2),
        ("amax", -2000000, -1000000, 50000, 1, 2),
        ("vmax", 1000000, 2000000, 50000, 1, 2),
        ("vmax", -2000000, -1000000, 50000, 1, 2),
        ("dmax", 1000000, 2000000, 50000, 1, 2),
        ("dmax", -2000000, -1000000, 50000, 1, 2),
    ],
)
def test_tmc5240_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("angular_position", "scale"),
        ("angular_velocity", "scale"),
        ("angular_acceleration", "scale"),
    ],
)
def test_tmc5240_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)
