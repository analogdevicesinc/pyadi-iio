import pytest

hardware = "fmcomms11"
classname = "adi.FMComms11"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_fmcomms11_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_fmcomms11_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 11)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(hardwaregain=-11.5),
        dict(hardwaregain=0),
        dict(hardwaregain=5),
        dict(hardwaregain=10),
        dict(hardwaregain=20),
    ],
)
def test_fmcomms11_cw_loopback(
    test_cw_loopback, iio_uri, classname, channel, param_set
):
    test_cw_loopback(iio_uri, classname, channel, param_set)
