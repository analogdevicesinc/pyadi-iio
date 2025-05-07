import pytest

hardware = "ad9172"
classname = "adi.ad9172"


@pytest.mark.skip(reason="GH random failure, not repeatable")
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9172_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)
