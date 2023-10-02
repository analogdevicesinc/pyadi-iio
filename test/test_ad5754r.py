import adi
import pytest

hardware = "ad5754r"
classname = "adi.ad5754r"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("int_ref_powerup", ["powerdown", "powerup"],),
        ("clear_setting", ["0v", "midscale_code"],),
        ("sdo_disable", ["enable", "disable"],),
    ],
)
def test_ad5754r_global_attr(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("powerup", ["powerdown", "powerup"],),
        (
            "range",
            [
                "0v_to_5v",
                "0v_to_10v",
                "0v_to_10v8",
                "neg5v_to_5v",
                "neg10v_to_10v",
                "neg10v8_to_10v8",
            ],
        ),
    ],
)
def test_ad5754r_channel_attr(iio_uri, classname, channel, attr, val):
    dev = adi.ad5754r(iio_uri)
    dev_chan = dev.channel[channel]
    for value in val:
        setattr(dev_chan, attr, value)
        val_read = getattr(dev_chan, attr)
        assert val_read == value
