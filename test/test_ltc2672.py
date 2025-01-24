import pytest

import adi
from adi.ltc2672 import *

hardware = "ltc2672"
classname = "adi.ltc2672"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "all_chns_span",
            [
                "off_mode",
                "3.125mA",
                "6.25mA",
                "12.5mA",
                "25mA",
                "50mA",
                "100mA",
                "200mA",
                "MVREF",
                "300mA",
            ],
        ),
        ("all_chns_powerdown", ["powerdown"],),
    ],
)
def test_ltc2672_global_attr(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "span",
            [
                "off_mode",
                "3.125mA",
                "6.25mA",
                "12.5mA",
                "25mA",
                "50mA",
                "100mA",
                "200mA",
                "MVREF",
                "300mA",
            ],
        ),
        ("powerdown", ["powerdown"],),
    ],
)
def test_ltc2672_channel_attr(iio_uri, classname, channel, attr, val):
    dev = adi.ltc2672(iio_uri)
    dev_chan = dev.channel[channel]
    for value in val:
        setattr(dev_chan, attr, value)
        val_read = getattr(dev_chan, attr)
        assert val_read == value
