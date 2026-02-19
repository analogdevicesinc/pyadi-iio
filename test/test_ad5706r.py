import pytest

import adi

hardware = "ad5706r"
classname = "adi.ad5706r"

#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("sampling_frequency", [10000, 50000, 100000, 200000, 500000],),
        ("addr_ascension", ["increment", "decrement"],),
        ("ref_select", ["internal", "external"],),
    ],
)
def test_ad5706r_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 1)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", ["current0", "current1", "current2", "current3"])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("hw_active_edge", ["rising_edge", "falling_edge", "any_edge"],),
        ("range_sel", ["50mA", "150mA", "200mA", "300mA",],),
        ("hw_func_sel", ["None", "LDAC", "Toggle", "Dither"],),
    ],
)
def test_ad5706r_channel_attr(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)
