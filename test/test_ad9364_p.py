import pytest

hardware = ["fmcomms4", "adrv9364"]
classname = "adi.ad9364"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain", -89.75, 0.0, 0.25, 0),
        ("rx_lo", 70000000, 6000000000, 1, 8),
        ("tx_lo", 70000000, 600000000, 1, 8),
        ("sample_rate", 2084000, 61440000, 1, 4),
    ],
)
def test_ad9364_attr(
    test_attribute_single_value, classname, hardware, attr, start, stop, step, tol
):
    test_attribute_single_value(classname, hardware, attr, start, stop, step, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("attr, tol", [("loopback", 0)])
@pytest.mark.parametrize("val", [0, 1, 2])
def test_ad9364_loopback_attr(
    test_attribute_single_value_str, classname, hardware, attr, val, tol
):
    test_attribute_single_value_str(classname, hardware, attr, val, tol)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
def test_ad9364_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
def test_ad9364_tx_data(test_dma_tx, classname, hardware, channel):
    test_dma_tx(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
def test_ad9364_cyclic_buffers(
    test_cyclic_buffer, classname, hardware, channel, param_set
):
    test_cyclic_buffer(classname, hardware, channel, param_set)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
def test_ad9364_cyclic_buffers_exception(
    test_cyclic_buffer_exception, classname, hardware, channel, param_set
):
    test_cyclic_buffer_exception(classname, hardware, channel, param_set)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
def test_ad9364_loopback(test_dma_loopback, classname, hardware, channel):
    test_dma_loopback(classname, hardware, channel)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_ad9364_sfdr(test_sfdr, classname, hardware, channel, param_set, sfdr_min):
    test_sfdr(classname, hardware, channel, param_set, sfdr_min)


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("frequency, scale", [(1000000, 1)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-30,
            sample_rate=4000000,
        )
    ],
)
@pytest.mark.parametrize("peak_min", [-40])
def test_ad9364_dds_loopback(
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
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=2000000000,
            rx_lo=2000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=3000000000,
            rx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
    ],
)
def test_ad9364_iq_loopback(test_iq_loopback, classname, hardware, channel, param_set):
    test_iq_loopback(classname, hardware, channel, param_set)
