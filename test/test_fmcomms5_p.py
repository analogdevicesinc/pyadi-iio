import pytest

hardware = "fmcomms5"
classname = "adi.FMComms5"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain", -86, 0.0, 0.25, 0),
        ("rx_lo", 70000000, 6000000000, 1, 8),
        ("tx_lo", 47000000, 6000000000, 1, 8),
        ("sample_rate", 2084000, 61440000, 1, 4),
    ],
)
def test_fmcomms5_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr, tol", [("loopback", 0)])
@pytest.mark.parametrize("val", [0, 1, 2])
def test_fmcomms5_loopback_attr(
    test_attribute_single_value_str, iio_uri, classname, attr, val, tol
):
    test_attribute_single_value_str(iio_uri, classname, attr, val, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_fmcomms5_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_fmcomms5_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_fmcomms5_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("frequency, scale", [(1000000, 1)])
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
        )
    ],
)
@pytest.mark.parametrize("peak_min", [-40])
def test_fmcomms5_dds_loopback(
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
        iio_uri, classname, param_set, channel, frequency, scale, peak_min
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
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
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_fmcomms5_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
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
            tx_lo=2000000000,
            rx_lo=2000000000,
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
    ],
)
def test_fmcomms5_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


# CHIP B TEST
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chip_b", -86, 0.0, 0.25, 0),
        ("rx_lo_chip_b", 70000000, 6000000000, 1, 8),
        ("tx_lo_chip_b", 47000000, 6000000000, 1, 8),
        ("sample_rate", 2084000, 61440000, 1, 4),
    ],
)
def test_fmcomms5_chip_b_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr, tol", [("loopback_chip_b", 0)])
@pytest.mark.parametrize("val", [0, 1, 2])
def test_fmcomms5_chip_b_loopback_attr(
    test_attribute_single_value_str, iio_uri, classname, attr, val, tol
):
    test_attribute_single_value_str(iio_uri, classname, attr, val, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2, 3, [2, 3]])
def test_fmcomms5_chip_b_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2, 3, [2, 3]])
def test_fmcomms5_chip_b_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2, 3])
def test_fmcomms5_chip_b_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2, 3])
@pytest.mark.parametrize("frequency, scale", [(1000000, 1)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo_chip_b=1500000000,
            rx_lo_chip_b=1500000000,
            gain_control_mode_chip_b_chan0="slow_attack",
            tx_hardwaregain_chip_b_chan0=-20,
            gain_control_mode_chip_b_chan1="slow_attack",
            tx_hardwaregain_chip_b_chan1=-20,
            sample_rate=4000000,
        ),
    ],
)
@pytest.mark.parametrize("peak_min", [-40])
def test_fmcomms5_dds_chip_b_loopback(
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
        iio_uri, classname, param_set, channel, frequency, scale, peak_min
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo_chip_b=1500000000,
            rx_lo_chip_b=1500000000,
            gain_control_mode_chip_b_chan0="slow_attack",
            tx_hardwaregain_chip_b_chan0=-20,
            gain_control_mode_chip_b_chan1="slow_attack",
            tx_hardwaregain_chip_b_chan1=-20,
            sample_rate=4000000,
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_fmcomms5_chip_b_sfdr(
    test_sfdr, iio_uri, classname, channel, param_set, sfdr_min
):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo_chip_b=1500000000,
            rx_lo_chip_b=1500000000,
            gain_control_mode_chip_b_chan0="slow_attack",
            tx_hardwaregain_chip_b_chan0=-20,
            gain_control_mode_chip_b_chan1="slow_attack",
            tx_hardwaregain_chip_b_chan1=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo_chip_b=2500000000,
            rx_lo_chip_b=2500000000,
            gain_control_mode_chip_b_chan0="slow_attack",
            tx_hardwaregain_chip_b_chan0=-20,
            gain_control_mode_chip_b_chan1="slow_attack",
            tx_hardwaregain_chip_b_chan1=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo_chip_b=3500000000,
            rx_lo_chip_b=3500000000,
            gain_control_mode_chip_b_chan0="slow_attack",
            tx_hardwaregain_chip_b_chan0=-20,
            gain_control_mode_chip_b_chan1="slow_attack",
            tx_hardwaregain_chip_b_chan1=-20,
            sample_rate=4000000,
        ),
    ],
)
def test_fmcomms5_chip_b_iq_loopback(
    test_iq_loopback, iio_uri, classname, channel, param_set
):
    test_iq_loopback(iio_uri, classname, channel, param_set)
