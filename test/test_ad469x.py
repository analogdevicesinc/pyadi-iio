import pytest

hardware = "ad4696"
classname = "adi.ad469x"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [["voltage0", "voltage1"]])
def test_ad469x_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 4)
