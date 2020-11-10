import pytest

hardware = "adrv9009-dual-fmcomms8"
classname = "adi.adrv9009_zu11eg_fmcomms8"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0_chip_c", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1_chip_c", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan0_chip_d", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1_chip_d", -41.95, 0.0, 0.05, 0.05),
        ("trx_lo_chip_c", 70000000, 6000000000, 1000, 0),
        ("trx_lo_chip_d", 70000000, 6000000000, 1000, 0),
    ],
)
def test_adrv9009_zu11eg_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
def test_adrv9009_zu11eg_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo_chip_c=1000000000,
            trx_lo_chip_d=5000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=3000000000,
            trx_lo_chip_d=4000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=5000000000,
            trx_lo_chip_d=1000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
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
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo_chip_c=1000000000,
            trx_lo_chip_d=1000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=3000000000,
            trx_lo_chip_d=1000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=5000000000,
            trx_lo_chip_d=1000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_rx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_chip_c=1,
            calibrate_rx_qec_en_chip_d=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_d=1,
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
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (
            dict(
                trx_lo_chip_c=1000000000,
                trx_lo_chip_d=1000000000,
                gain_control_mode_chan0_chip_c="manual",
                gain_control_mode_chan1_chip_c="manual",
                gain_control_mode_chan0_chip_d="manual",
                gain_control_mode_chan1_chip_d="manual",
                rx_hardwaregain_chan0_chip_c=0,
                rx_hardwaregain_chan1_chip_c=0,
                rx_hardwaregain_chan0_chip_d=0,
                rx_hardwaregain_chan1_chip_d=0,
                tx_hardwaregain_chan0_chip_c=-10,
                tx_hardwaregain_chan1_chip_c=-10,
                tx_hardwaregain_chan0_chip_d=-10,
                tx_hardwaregain_chan1_chip_d=-10,
                calibrate_tx_qec_en_chip_c=1,
                calibrate_tx_qec_en_chip_d=1,
                calibrate_chip_c=1,
                calibrate_chip_d=1,
            ),
            0.5,
            20,
            60,
        ),
        (
            dict(
                trx_lo_chip_c=1000000000,
                trx_lo_chip_d=1000000000,
                gain_control_mode_chan0_chip_c="manual",
                gain_control_mode_chan1_chip_c="manual",
                gain_control_mode_chan0_chip_d="manual",
                gain_control_mode_chan1_chip_d="manual",
                rx_hardwaregain_chan0_chip_c=30,
                rx_hardwaregain_chan1_chip_c=30,
                rx_hardwaregain_chan0_chip_d=30,
                rx_hardwaregain_chan1_chip_d=30,
                tx_hardwaregain_chan0_chip_c=-10,
                tx_hardwaregain_chan1_chip_c=-10,
                tx_hardwaregain_chan0_chip_d=-10,
                tx_hardwaregain_chan1_chip_d=-10,
                calibrate_tx_qec_en_chip_c=1,
                calibrate_tx_qec_en_chip_d=1,
                calibrate_chip_c=1,
                calibrate_chip_d=1,
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
    test_gain_check(
        iio_uri, classname, channel, param_set, dds_scale, min_rssi, max_rssi
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo_chip_c=1000000000,
            trx_lo_chip_d=5000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-20,
            tx_hardwaregain_chan1_chip_c=-20,
            tx_hardwaregain_chan0_chip_d=-20,
            tx_hardwaregain_chan1_chip_d=-20,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_c=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=3000000000,
            trx_lo_chip_d=4000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-20,
            tx_hardwaregain_chan1_chip_c=-20,
            tx_hardwaregain_chan0_chip_d=-20,
            tx_hardwaregain_chan1_chip_d=-20,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_c=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=5000000000,
            trx_lo_chip_d=1000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            tx_hardwaregain_chan0_chip_c=-20,
            tx_hardwaregain_chan1_chip_c=-20,
            tx_hardwaregain_chan0_chip_d=-20,
            tx_hardwaregain_chan1_chip_d=-20,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_c=1,
            calibrate_chip_d=1,
        ),
    ],
)
def test_adrv9009_zu11eg_iq_loopback(
    test_iq_loopback, iio_uri, classname, channel, param_set
):
    test_iq_loopback(iio_uri, classname, channel, param_set)
