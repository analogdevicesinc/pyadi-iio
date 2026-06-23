import pytest

hardware = "ad7091r8"
classname = "adi.ad7091rx"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["raw"])
@pytest.mark.parametrize(
    "channel",
    [
        "voltage0",
        "voltage1",
        "voltage2",
        "voltage3",
        "voltage4",
        "voltage5",
        "voltage6",
        "voltage7",
    ],
)
def test_ad7091rx_channel_attr_raw(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)
