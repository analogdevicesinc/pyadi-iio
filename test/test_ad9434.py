import pytest

hardware = "ad9434"
classname = "adi.ad9434"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad9434_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["test_mode"])
@pytest.mark.parametrize(
    "val",
    [
        "off",
        "midscale_short",
        "pos_fullscale",
        "neg_fullscale",
        "checkerboard",
        "pn_long",
        "pn_short",
        "one_zero_toggle",
        "user",
    ],
)
def test_ad9434_loopback_attr(
    test_attribute_single_value_str, iio_uri, classname, attr, val
):
    test_attribute_single_value_str(iio_uri, classname, attr, val, 0)
