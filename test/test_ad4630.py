import pytest

import adi

hardware = ["ad4030-24", "ad4630-24"]
classname = "adi.ad4630"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [[0, 1]])
def test_ad4630_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sample_rate",
            [10000, 50000, 100000, 200000, 500000, 1000000, 1750000, 2000000],
        ),
    ],
)
def test_ad4630_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 1)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("calibbias", 0, 2, 1, 0, 2, "chan0"),
        ("calibbias", 0, 2, 1, 0, 2, "chan1"),
        ("calibscale", 0, 1, 0.5, 0, 2, "chan0"),
        ("calibscale", 0, 1, 0.5, 0, 2, "chan1"),
    ],
)
def test_ad4630_channel_attrs(
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


hardware = ["adaq4224"]
classname = "adi.adaq42xx"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, avail_attr, tol, repeats, sub_channel",
    [("scale", "scale_available", 0, 1, "chan0",),],
)
def test_adaq42xx_scale_attr(
    test_attribute_multiple_values,
    iio_uri,
    classname,
    attr,
    avail_attr,
    tol,
    repeats,
    sub_channel,
):
    # Get the device
    sdr = eval(classname + "(uri='" + iio_uri + "')")

    # Check hardware
    if not hasattr(sdr, sub_channel):
        raise AttributeError(sub_channel + " not defined in " + classname)
    if not hasattr(getattr(sdr, sub_channel), avail_attr):
        raise AttributeError(avail_attr + " not defined in " + classname)

    # Get the list of available scale values
    val = getattr(getattr(sdr, sub_channel), avail_attr)

    test_attribute_multiple_values(
        iio_uri, classname, attr, val, tol, repeats, sub_channel=sub_channel
    )
