import pytest

hardware = ["ad3552r"]
classname = "adi.ad3552r"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad3552r_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)
