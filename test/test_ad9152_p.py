import pytest

hardware = "daq3"
classname = "adi.ad9152"


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9152_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)