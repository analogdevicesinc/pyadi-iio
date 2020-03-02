import pytest

hardware = "daq3"
classname = "adi.DAQ3"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_daq3_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_daq3_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("frequency, scale", [(200000000, 0.5)])
@pytest.mark.parametrize("param_set", [dict()])
@pytest.mark.parametrize("peak_min", [-40])
def test_daq3_dds_loopback(
    test_dds_loopback,
    classname,
    hardware,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
):
    test_dds_loopback(
        classname, hardware, param_set, channel, frequency, scale, peak_min
    )


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("param_set", [dict()])
def test_daq3_cw_loopback(test_cw_loopback, classname, hardware, channel, param_set):
    test_cw_loopback(classname, hardware, channel, param_set)
