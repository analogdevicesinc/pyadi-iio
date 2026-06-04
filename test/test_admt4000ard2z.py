import iio
import pytest

import adi

hardware = ["admt4000ard2z"]
classname = "adi.admt4000ard2z"


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
def test_admt4000ard2z_attr_boolean_readonly(
    test_attribute_single_value_boolean_readonly, iio_uri, classname, attr
):
    do_mock()
    test_attribute_single_value_boolean_readonly(iio_uri, classname, attr)


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value, depends",
    [
        ("magnetic_reset", 1, {"_disable_dc_dc_after_reset": True}),
        ("magnetic_reset", 1, {"_disable_dc_dc_after_reset": False}),
    ],
)
def test_admt4000ard2z_attr_write_only(
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
def test_admt4000ard2z_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    do_mock()
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_admt4000ard2z_attr_readonly_gpio(iio_uri, classname):
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
def test_admt4000ard2z_attr_single_str(
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
def test_admt4000ard2z_attr_harmonics(iio_uri, classname, attr, val):
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
