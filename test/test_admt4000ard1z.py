import iio
import pytest

import adi

hardware = ["admt4000ard1z"]
classname = "adi.admt4000ard1z"


def do_mock():
    def mock_set_trigger(self, value):
        pass

    # Mock the _set_trigger method in iio.Device
    iio.Device._set_trigger = mock_set_trigger


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("shutdown_pulse"), ("power_enable"), ("coil_reset"),],
)
def test_admt4000ard1z_attr_boolean_readonly(
    test_attribute_single_value_boolean_readonly, iio_uri, classname, attr
):
    do_mock()
    test_attribute_single_value_boolean_readonly(iio_uri, classname, attr)


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value", [("magnetic_reset", 1), ("motor_sensor_alignment", 1),],
)
def test_admt4000ard1z_attr_write_only(
    test_attribute_write_only_str, iio_uri, classname, attr, value,
):
    do_mock()
    test_attribute_write_only_str(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("sensor.turns", "raw"),
        ("sensor.angle", "raw"),
        ("sensor.temp", "raw"),
        ("sensor.cosine", "raw"),
        ("sensor.sine", "raw"),
        ("sensor.radius", "raw"),
        ("sensor.turns", "scale"),
        ("sensor.angle", "scale"),
        ("sensor.temp", "scale"),
        ("sensor.radius", "scale"),
        ("sensor.temp", "offset"),
        ("sensor.turns", "processed"),
        ("sensor.angle", "processed"),
        ("sensor.temp", "processed"),
        ("sensor", "faults"),
    ],
)
def test_admt4000ard1z_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    do_mock()
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_admt4000ard1z_attr_readonly_gpio(iio_uri, classname):
    do_mock()
    dev = eval(classname + "(uri='" + iio_uri + "').sensor")
    assert len(dev.gpio) == 6
    for gpio in dev.gpio:
        assert gpio is not None


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("conversion_mode", 0, 1, 1, 0, 2, "sensor"),
        ("angle_filter_enable", 0, 1, 1, 0, 2, "sensor"),
    ],
)
def test_admt4000ard1z_attr_single_str(
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
    do_mock()
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "harmonics",
            [
                0.42305706499276774,
                157.40035229531108,
                0.3952010904372606,
                127.2546108682859,
                0.8250752450613099,
                124.40225451585263,
                0.8811647734156018,
                52.10340522521499,
            ],
        ),
        (
            "harmonics",
            [
                (0.6881799701516068, 7.6301230012092836),
                (0.5933649687824497, 356.95785043140296),
                (0.4485499122685841, 64.86013946791675),
                (0.23903747446272405, 320.40388424169925),
            ],
        ),
    ],
)
def test_admt4000ard1z_attr_harmonics(iio_uri, classname, attr, val):
    do_mock()
    dev = eval(classname + "(uri='" + iio_uri + "').sensor")
    setattr(dev, attr, val)
    res = getattr(dev, attr)
    res = [item for tup in res for item in tup]
    if isinstance(val[0], tuple):
        val = [item for tup in val for item in tup]
    for i in range(len(val)):
        if i % 2 == 0:
            assert abs(val[i] - res[i]) < 0.1
        else:
            assert abs(val[i] - res[i]) < 60


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value, depends",
    [
        ("rotate_relative_usteps", 50000, {"motor_sensor_alignment": 1}),
        ("rotate_relative_usteps", -50000, {"motor_sensor_alignment": 1}),
        ("rotate_relative_angle", 90, {"motor_sensor_alignment": 1}),
        ("rotate_relative_angle", -90, {"motor_sensor_alignment": 1}),
        ("rotate_absolute_angle", 180, {"motor_sensor_alignment": 1}),
    ],
)
def test_admt4000ard1z_attr_write_only_with_depends(
    test_attribute_write_only_str_with_depends, iio_uri, classname, attr, value, depends
):
    do_mock()
    test_attribute_write_only_str_with_depends(iio_uri, classname, attr, value, depends)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("motor.angular_acceleration", "raw"),
        ("motor.angular_velocity", "raw"),
        ("motor.angular_position", "raw"),
        ("motor.angular_acceleration", "scale"),
        ("motor.angular_velocity", "scale"),
        ("motor.angular_position", "scale"),
        ("motor.angular_acceleration", "calibscale"),
        ("motor.angular_velocity", "calibscale"),
        ("motor.angular_position", "calibscale"),
        ("motor.angular_position", "preset"),
        ("motor", "amax"),
        ("motor", "dmax"),
        ("motor", "vmax"),
        ("motor", "a1"),
        ("motor", "a2"),
        ("motor", "d1"),
        ("motor", "d2"),
        ("motor", "v1"),
        ("motor", "v2"),
        ("motor", "vstart"),
        ("motor", "vstop"),
        ("motor", "direction"),
    ],
)
def test_admt4000ard1z_motor_readonly_attr(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr,
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)
