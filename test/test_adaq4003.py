import adi
import pytest

hardware = "adaq4003"
classname = "adi.adaq4003"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "sampling_frequency",
            [10000, 50000, 100000, 200000, 500000, 1000000, 2000000],
        ),
    ],
)
def test_adaq4003_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):

    # Setting the sampling frequency is only possible through FPGA implemented
    # hardware (SPI-Engine offload) so the attribute might not exist if the
    # the platform is not set with proper FPGA bitstream or doesn't have
    # a integrated FPGA.

    try:
        test_attribute_multiple_values(iio_uri, classname, attr, val, 1)
    except KeyError:
        pytest.skip("sampling_frequency attribute not available on test platform.")


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, avail_attr, tol, repeats, sub_channel",
    [("scale", "scale_available", 0, 1, "voltage0-voltage1",),],
)
def test_adaq4003_scale_attr(
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


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_adaq4003_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 15)
