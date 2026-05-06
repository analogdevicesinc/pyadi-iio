import iio
import pytest

hardware = ["tmc5240"]
classname = "adi.tmc5240"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("angular_acceleration", "raw"),
        ("angular_velocity", "raw"),
        ("angular_position", "raw"),
        ("angular_acceleration", "scale"),
        ("angular_velocity", "scale"),
        ("angular_position", "scale"),
        ("angular_acceleration", "calibscale"),
        ("angular_velocity", "calibscale"),
        ("angular_position", "calibscale"),
        ("angular_position", "preset"),
    ],
)
def test_tmc5240_ch_attr(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr,
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, depends, start, stop",
    [
        ("amax", [], 0, 2 ** 18 - 1),
        ("dmax", [], 0, 2 ** 18 - 1),
        ("vmax", [], 0, 2 ** 23 - 512),
        ("a1", [], 0, 2 ** 18 - 1),
        ("a2", [], 0, 2 ** 18 - 1),
        ("d1", [], 0, 2 ** 18 - 1),
        ("d2", [], 0, 2 ** 18 - 1),
        ("v1", [], 0, 2 ** 20 - 1),
        ("v2", [], 0, 2 ** 20 - 1),
        ("vstart", [], 0, 2 ** 18 - 1),
        ("vstop", [], 0, 2 ** 18 - 1),
        ("direction", [], -1, 1),
    ],
)
def test_tmc5240_attr(
    test_attribute_check_range_readonly_with_depends,
    iio_uri,
    classname,
    attr,
    depends,
    start,
    stop,
):
    test_attribute_check_range_readonly_with_depends(
        iio_uri, classname, attr, depends, start, stop
    )
