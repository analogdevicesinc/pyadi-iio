import pytest

hardware = "daq2"
classname = "adi.ad9144"


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9144_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)
