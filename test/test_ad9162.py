import pytest

# AD9162 isn't in the adi_hardware_map.py in pylibiio
hardware = ["ad9162", "fmcomms11"]
classname = "adi.ad9162"


@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9162_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)
