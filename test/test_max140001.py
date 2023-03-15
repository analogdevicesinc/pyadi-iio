import pytest

hardware = "max140001"
classname = "adi,max140001"


######################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_max140001_rx_data (test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)