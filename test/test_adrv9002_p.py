import pytest

hardware = "adrv9002"
classname = "adi.adrv9002"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain", -89.75, 0.0, 0.25, 0),
        ("rx1_lo", 70000000, 6000000000, 1, 8),
        ("tx1_lo", 47000000, 6000000000, 1, 8),
    ],
)
def test_adrv9002_attr(
    test_attribute_single_value, classname, hardware, attr, start, stop, step, tol
):
    test_attribute_single_value(classname, hardware, attr, start, stop, step, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
def test_adrv9002_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
def test_adrv9002_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx1_lo=1000000000,
            rx1_lo=1000000000,
            interface_gain_chan0="-12dB",
            interface_gain_chan1="-12dB",
            rx_ensm_mode_chan0="rf_enabled",
            rx_ensm_mode_chan1="rf_enabled",
            tx_hardwaregain_chan0=-20,
            tx_ensm_mode_chan0="rf_enabled",
            tx_cyclic_buffer=True,
        )
    ],
)
def test_adrv9002_cw_loopback(
    test_cw_loopback, classname, hardware, channel, param_set
):
    test_cw_loopback(classname, hardware, channel, param_set)
