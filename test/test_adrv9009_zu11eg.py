import pytest

hardware = "adrv9009-dual"
classname = "adi.adrv9009_zu11eg"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan0_chip_b", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1_chip_b", -41.95, 0.0, 0.05, 0.05),
        ("trx_lo", 70000000, 6000000000, 1000, 0),
        ("trx_lo_chip_b", 70000000, 6000000000, 1000, 0),
    ],
)
def test_adrv9009_zu11eg_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(4))
def test_adrv9009_zu11eg_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            trx_lo_chip_b=5000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=3000000000,
            trx_lo_chip_b=4000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
    ],
)
@pytest.mark.parametrize("sfdr_min", [45])
def test_adrv9009_zu11eg_sfdr(
    test_sfdr, iio_uri, classname, channel, param_set, sfdr_min
):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=3000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
            calibrate_rx_qec_en_chip_b=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate_chip_b=1,
        ),
    ],
)
@pytest.mark.parametrize("dds_scale, min_rssi, max_rssi", [(0, 35, 60), (0.9, 0, 22)])
def test_adrv9009_zu11eg_dds_gain_check_agc(
    test_gain_check,
    iio_uri,
    classname,
    channel,
    param_set,
    dds_scale,
    min_rssi,
    max_rssi,
):
    test_gain_check(
        iio_uri, classname, channel, param_set, dds_scale, min_rssi, max_rssi
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (
            dict(
                trx_lo=1000000000,
                trx_lo_chip_b=1000000000,
                gain_control_mode_chan0="manual",
                gain_control_mode_chan1="manual",
                gain_control_mode_chan0_chip_b="manual",
                gain_control_mode_chan1_chip_b="manual",
                rx_hardwaregain_chan0=0,
                rx_hardwaregain_chan1=0,
                rx_hardwaregain_chan0_chip_b=0,
                rx_hardwaregain_chan1_chip_b=0,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                tx_hardwaregain_chan0_chip_b=-10,
                tx_hardwaregain_chan1_chip_b=-10,
                calibrate_tx_qec_en=1,
                calibrate_tx_qec_en_chip_b=1,
                calibrate=1,
                calibrate_chip_b=1,
            ),
            0.5,
            20,
            60,
        ),
        (
            dict(
                trx_lo=1000000000,
                gain_control_mode_chan0="manual",
                gain_control_mode_chan1="manual",
                gain_control_mode_chan0_chip_b="manual",
                gain_control_mode_chan1_chip_b="manual",
                rx_hardwaregain_chan0=30,
                rx_hardwaregain_chan1=30,
                rx_hardwaregain_chan0_chip_b=30,
                rx_hardwaregain_chan1_chip_b=30,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                tx_hardwaregain_chan0_chip_b=-10,
                tx_hardwaregain_chan1_chip_b=-10,
                calibrate_tx_qec_en=1,
                calibrate_tx_qec_en_chip_b=1,
                calibrate=1,
                calibrate_chip_b=1,
            ),
            0.5,
            0,
            15,
        ),
    ],
)
def test_adrv9009_zu11eg_dds_gain_check_vary_power(
    test_gain_check,
    iio_uri,
    classname,
    channel,
    param_set,
    dds_scale,
    min_rssi,
    max_rssi,
):
    test_gain_check(classname, channel, param_set, dds_scale, min_rssi, max_rssi)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            trx_lo_chip_b=5000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_hardwaregain_chan0_chip_b=-20,
            tx_hardwaregain_chan1_chip_b=-20,
            calibrate_tx_qec_en=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=3000000000,
            trx_lo_chip_b=4000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_hardwaregain_chan0_chip_b=-20,
            tx_hardwaregain_chan1_chip_b=-20,
            calibrate_tx_qec_en=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate=1,
            calibrate_chip_b=1,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_hardwaregain_chan0_chip_b=-20,
            tx_hardwaregain_chan1_chip_b=-20,
            calibrate_tx_qec_en=1,
            calibrate_tx_qec_en_chip_b=1,
            calibrate=1,
            calibrate_chip_b=1,
        ),
    ],
)
def test_adrv9009_zu11eg_iq_loopback(
    test_iq_loopback, iio_uri, classname, channel, param_set
):
    test_iq_loopback(iio_uri, classname, channel, param_set)
