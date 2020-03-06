# 	Required Test setup:
#
#	- ZFRSC-123+ splitter is used to distribute
#	the port A of TX to port A of RX and TXM channel
#	- port B of TX will be connected to port B of RX channel
#
# 							(1) -> RX1A
# 	TX1A -> (S) ZFRSC-123+
# 							(2) -> TXM1
#	-----------------------------------
#	TX1B -> RX1B
#	-----------------------------------
# 							(1) -> RX2A
# 	TX2A -> (S) ZFRSC-123+
# 							(2) -> TXM2
#	-----------------------------------
#	TX2B -> RX2B

import pytest
import time

hardware = "ad9361"
classname = "adi.ad9361"

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain", -89.75, 0.0, 0.25, 0),
        ("rx_lo", 70000000, 6000000000, 1, 8),
        ("tx_lo", 47000000, 6000000000, 1, 8),
        ("sample_rate", 2084000, 61440000, 1, 4),
    ],
)
def test_ad9361_attr(
    test_attribute_single_value, classname, hardware, attr, start, stop, step, tol
):
    test_attribute_single_value(classname, hardware, attr, start, stop, step, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("attr, tol", [("loopback", 0)])
@pytest.mark.parametrize("val", [0, 1, 2])
def test_ad9361_loopback_attr(
    test_attribute_single_value_str, classname, hardware, attr, val, tol
):
    test_attribute_single_value_str(classname, hardware, attr, val, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9361_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9361_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
def test_ad9361_loopback(test_dma_loopback, classname, hardware, channel):
    test_dma_loopback(classname, hardware, channel)

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_port_select = "TX_MONITOR1_2",
                gain_control_mode_chan0="slow_attack",
                tx_port_select="A",
                tx_hardwaregain_chan0=0,
                tx_hardwaregain_chan1=0,
                sample_rate=30720000,
            ),
            0.5,
            27,
            34
        )
    ]
)
def test_ad9361_TPM_rssi(test_gain_check, classname, hardware, channel, param_set, dds_scale, min_rssi, max_rssi):
    test_gain_check(classname, hardware, channel, param_set, dds_scale, min_rssi, max_rssi)

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1800000000,
            rx_lo=1800000000,
            rx_port_select = "B_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="B",
            tx_hardwaregain_chan0=-10,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-10,
            sample_rate=30720000,
        ),
        dict(
            tx_lo=1800000000,
            rx_lo=1800000000,
            rx_port_select = "A_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="A",
            tx_hardwaregain_chan0=0,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=0,
            sample_rate=30720000,
        ),
        dict(
            tx_lo=3500000000,
            rx_lo=3500000000,
            rx_port_select = "B_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="B",
            tx_hardwaregain_chan0=-10,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-10,
            sample_rate=30720000,
        ),
        dict(
            tx_lo=3500000000,
            rx_lo=3500000000,
            rx_port_select = "A_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="A",
            tx_hardwaregain_chan0=0,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=0,
            sample_rate=30720000,
        ),
        dict(
            tx_lo=5500000000,
            rx_lo=5500000000,
            rx_port_select = "B_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="B",
            tx_hardwaregain_chan0=-10,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-10,
            sample_rate=30720000,
        ),
        dict(
            tx_lo=5500000000,
            rx_lo=5500000000,
            rx_port_select = "A_BALANCED",
            gain_control_mode_chan0="slow_attack",
            tx_port_select="A",
            tx_hardwaregain_chan0=0,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=0,
            sample_rate=30720000,
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [50])
def test_ad9361_sfdr(test_sfdr, classname, hardware, channel, param_set, sfdr_min):
    test_sfdr(classname, hardware, channel, param_set, sfdr_min)

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=3000000000,
            rx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=5000000000,
            rx_lo=5000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
            sample_rate=4000000,
        ),
    ],
)
def test_ad9361_iq_loopback(test_iq_loopback, classname, hardware, channel, param_set):
    test_iq_loopback(classname, hardware, channel, param_set)