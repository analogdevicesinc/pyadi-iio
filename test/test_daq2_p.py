import pytest

hardware = "daq2"
classname = "adi.DAQ2"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_daq2_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_daq2_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 11)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("param_set", [dict()])
@pytest.mark.parametrize(
    "frequency, scale, peak_min",
    [
        (5000000, 0.12, -55),
        (10000000, 0.06, -61),
        (10000000, 0.12, -55),
        (15000000, 0.12, -61),
        (15000000, 0.5, -42),
        (200000000, 0.5, -42),
    ],
)
def test_daq2_dds_loopback(
    test_dds_loopback,
    iio_uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
):
    test_dds_loopback(
        iio_uri,
        classname,
        param_set,
        channel,
        frequency,
        scale,
        peak_min,
        useWindow=True,
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set", [dict(),],
)
def test_daq2_cw_loopback(test_cw_loopback, iio_uri, classname, channel, param_set):
    test_cw_loopback(iio_uri, classname, channel, param_set)
