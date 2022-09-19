import adi
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


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(4))
def test_adrv9009_zu11eg_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "low, high",
    [([-50.0, -120.0, -120.0, -120.0, -120.0], [-5.0, -50.0, -60.0, -70.0, -70.0])],
)
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            ensm_mode="radio_off",
            trx_lo=1000000000,
            trx_lo_chip_b=5000000000,
            obs_powerdown_en=1,
            obs_powerdown_en_chan1=1,
            obs_powerdown_en_chip_b=1,
            obs_powerdown_en_chan1_chip_b=1,
            rx_powerdown_en_chan0=0,
            rx_powerdown_en_chan1=0,
            rx_powerdown_en_chan0_chip_b=0,
            rx_powerdown_en_chan1_chip_b=0,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
        ),
        dict(
            trx_lo=3000000000,
            trx_lo_chip_b=4000000000,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
        ),
    ],
)
def test_adrv9009_zu11eg_sfdr(
    test_sfdrl, classname, iio_uri, channel, param_set, low, high
):
    test_sfdrl(classname, iio_uri, channel, param_set, low, high, plot=True)


#########################################
# @pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "low, high",
    [([-50.0, -120.0, -120.0, -120.0, -120.0], [5.0, -50.0, -60.0, -70.0, -70.0])],
)
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            ensm_mode="radio_on",
            trx_lo=2500000000,
            trx_lo_chip_b=2500000000,
            rx_powerdown_en_chan0=1,
            rx_powerdown_en_chan1=1,
            rx_powerdown_en_chan0_chip_b=1,
            rx_powerdown_en_chan1_chip_b=1,
            obs_powerdown_en=0,
            obs_powerdown_en_chan1=0,
            obs_powerdown_en_chip_b=0,
            obs_powerdown_en_chan1_chip_b=0,
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            aux_obs_lo=2500000000,
            obs_rf_port_select="OBS_TX_LO",
        ),
    ],
)
def test_adrv9009_zu11eg_sfdr_for_obs(
    test_sfdrl, classname, iio_uri, channel, param_set, low, high
):
    test_sfdrl(
        classname, iio_uri, channel, param_set, low, high, plot=True, use_obs=True
    )


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            ensm_mode="radio_off",
            trx_lo=1000000000,
            trx_lo_chip_b=5000000000,
            obs_powerdown_en=1,
            obs_powerdown_en_chan1=1,
            obs_powerdown_en_chip_b=1,
            obs_powerdown_en_chan1_chip_b=1,
            rx_powerdown_en_chan0=0,
            rx_powerdown_en_chan1=0,
            rx_powerdown_en_chan0_chip_b=0,
            rx_powerdown_en_chan1_chip_b=0,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            gain_control_mode_chan0_chip_b="slow_attack",
            gain_control_mode_chan1_chip_b="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
        ),
        dict(
            trx_lo=3000000000,
            trx_lo_chip_b=4000000000,
        ),
        dict(
            trx_lo=5000000000,
            trx_lo_chip_b=1000000000,
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
@pytest.mark.parametrize("rx_buffer_size", [128, 256, 512, 1024])
@pytest.mark.parametrize("rx_enabled_channels", [[0], [0, 1], [0, 1, 2, 3]])
def test_adrv9009_zu11eg_buffer_size(iio_uri, rx_buffer_size, rx_enabled_channels):
    dev = adi.adrv9009_zu11eg(iio_uri)
    dev.rx_buffer_size = rx_buffer_size
    dev.rx_enabled_channels = rx_enabled_channels

    data = dev.rx()
    if len(rx_enabled_channels) == 1:
        assert len(data) == rx_buffer_size
    else:
        for chan in data:
            assert len(chan) == rx_buffer_size
