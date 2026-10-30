import pytest

hardware = "max14906"
classname = "adi.max14906"


@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", ["voltage0"])
@pytest.mark.parametrize(
    "attr, val", [("raw", [0, 1])],
)
def test_max14906_channel_attr(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)
