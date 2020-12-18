import pytest

try:
    import adi.jesd

    skip_jesd = False
except:
    skip_jesd = True


hardware = "adrv9009"
classname = "adi.adrv9009"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1", -41.95, 0.0, 0.05, 0.05),
        ("trx_lo", 70000000, 6000000000, 1000, 0),
    ],
)
def test_adrv9009_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_adrv9009_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=5000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
    ],
)
@pytest.mark.parametrize("sfdr_min", [45])
def test_adrv9009_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=5000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            calibrate_rx_qec_en=1,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
    ],
)
@pytest.mark.parametrize("dds_scale, min_rssi, max_rssi", [(0, 35, 60), (0.9, 0, 22)])
def test_adrv9009_dds_gain_check_agc(
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
                gain_control_mode_chan0="manual",
                gain_control_mode_chan1="manual",
                rx_hardwaregain_chan0=0,
                rx_hardwaregain_chan1=0,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                calibrate_tx_qec_en=1,
                calibrate=1,
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
                rx_hardwaregain_chan0=30,
                rx_hardwaregain_chan1=30,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                calibrate_tx_qec_en=1,
                calibrate=1,
            ),
            0.5,
            0,
            15,
        ),
    ],
)
def test_adrv9009_dds_gain_check_vary_power(
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
    "param_set",
    [
        dict(
            trx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            calibrate_tx_qec_en=1,
            calibrate=1,
        ),
    ],
)
def test_adrv9009_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.skipif(skip_jesd, reason="JESD module not importable")
@pytest.mark.iio_hardware(hardware)
def test_adrv9009_jesd(iio_uri):
    import adi

    sdr = adi.adrv9009(uri=iio_uri, jesd_monitor=True)
    info = sdr._jesd.get_all_statuses()
    assert info
