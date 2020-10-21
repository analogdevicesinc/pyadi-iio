import pytest

hardware = "daq2"
classname = "adi.ad9680"


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9680_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)
