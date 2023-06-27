import pytest

hardware = ["packrf", "adrv9361", "fmcomms2", "ad9361"]
classname = "adi.ad9361"

params = dict(
    one_cw_tone_manual=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    one_cw_tone_slow_attack=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_attenuation_20dB_slow_attack=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-20,
        tx_hardwaregain_chan1=-20,
    ),
    change_attenuation_0dB_slow_attack=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    change_sampling_rate_60MSPS_slow_attack=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=60710000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_sampling_rate_15MSPS_slow_attack=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=15000000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_attenuation_10dB_manual=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_attenuation_5dB_manual=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        tx_hardwaregain_chan0=-5,
        tx_hardwaregain_chan1=-5,
    ),
    change_rf_gain_5dB_manual=dict(
        tx_lo=2300000000,
        rx_lo=2300000000,
        sample_rate=30720000,
        tx_rf_bandwidth=18000000,
        rx_rf_bandwidth=18000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        rx_hardwaregain_chan0=5,
        rx_hardwaregain_chan1=5,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("tx_hardwaregain_chan0", -89.75, 0.0, 0.25, 0, 100),
        ("tx_hardwaregain_chan1", -89.75, 0.0, 0.25, 0, 100),
        ("rx_lo", 70000000, 6000000000, 1, 8, 100),
        ("tx_lo", 47000000, 6000000000, 1, 8, 100),
        ("sample_rate", 2084000, 61440000, 1, 4, 20),
        ("loopback", 0, 0, 1, 0, 0),
        ("loopback", 1, 1, 1, 0, 0),
        ("loopback", 2, 2, 1, 0, 0),
    ],
)
def test_ad9361_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9361_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad9361_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_ad9361_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set, sfdr_min",
    [
        (
            dict(
                sample_rate=4000000,
                tx_lo=1000000000,
                rx_lo=1000000000,
                gain_control_mode_chan0="slow_attack",
                tx_hardwaregain_chan0=-20,
                gain_control_mode_chan1="slow_attack",
                tx_hardwaregain_chan1=-20,
            ),
            40,
        ),
        (params["one_cw_tone_manual"], 23),
        (params["change_attenuation_10dB_manual"], 37),
        (params["change_attenuation_5dB_manual"], 25),
        (params["change_rf_gain_5dB_manual"], 22),
        (params["one_cw_tone_slow_attack"], 23),
        (params["change_attenuation_20dB_slow_attack"], 43),
        (params["change_attenuation_0dB_slow_attack"], 23),
        (params["change_sampling_rate_60MSPS_slow_attack"], 48),
        (params["change_sampling_rate_15MSPS_slow_attack"], 52),
    ],
)
def test_ad9361_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            sample_rate=4000000,
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
        ),
        dict(
            sample_rate=4000000,
            tx_lo=2000000000,
            rx_lo=2000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
        ),
        dict(
            sample_rate=4000000,
            tx_lo=3000000000,
            rx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan1=-20,
        ),
        params["one_cw_tone_manual"],
        params["change_attenuation_10dB_manual"],
        params["change_attenuation_5dB_manual"],
        params["change_rf_gain_5dB_manual"],
        params["one_cw_tone_slow_attack"],
        params["change_attenuation_20dB_slow_attack"],
        params["change_attenuation_0dB_slow_attack"],
        params["change_sampling_rate_60MSPS_slow_attack"],
        params["change_sampling_rate_15MSPS_slow_attack"],
    ],
)
def test_ad9361_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_manual"], 0.12, 23.25, 27.5),
        (params["one_cw_tone_manual"], 0.25, 17, 23),
        (params["one_cw_tone_manual"], 0.06, 28, 34.5),
        (params["change_rf_gain_5dB_manual"], 0.25, 20, 25.5),
        (params["change_attenuation_10dB_manual"], 0.25, 25, 32),
        (params["change_attenuation_5dB_manual"], 0.25, 21, 26.5),
    ],
)
def test_ad9361_dds_gain_check_vary_power(
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
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_slow_attack"], 0.06, 41.75, 50),
        (params["change_attenuation_20dB_slow_attack"], 0.06, 53, 56.75),
        (params["change_attenuation_0dB_slow_attack"], 0.06, 32, 37.5),
    ],
)
def test_ad9361_dds_gain_check_agc(
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
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min",
    [
        (params["one_cw_tone_manual"], 2000000, 0.12, -47),
        (params["one_cw_tone_manual"], 2000000, 0.25, -43),
        (params["one_cw_tone_manual"], 2000000, 0.06, -53),
        (params["change_attenuation_10dB_manual"], 2000000, 0.25, -50),
        (params["change_attenuation_5dB_manual"], 2000000, 0.25, -45.5),
        (params["change_rf_gain_5dB_manual"], 2000000, 0.25, -36),
        (params["one_cw_tone_slow_attack"], 500000, 0.06, -41.5),
        (params["one_cw_tone_slow_attack"], 1000000, 0.06, -41.5),
        (params["one_cw_tone_slow_attack"], 2000000, 0.06, -41.5),
        (params["one_cw_tone_slow_attack"], 2000000, 0.12, -41.5),
        (params["one_cw_tone_slow_attack"], 3000000, 0.25, -41.5),
        (params["one_cw_tone_slow_attack"], 4000000, 0.5, -41.5),
        (params["change_sampling_rate_60MSPS_slow_attack"], 2000000, 0.06, -41.5),
        (params["change_sampling_rate_15MSPS_slow_attack"], 2000000, 0.06, -41.5),
        (params["change_attenuation_20dB_slow_attack"], 1000000, 0.06, -43),
        (params["change_attenuation_0dB_slow_attack"], 1000000, 0.06, -43),
    ],
)
def test_ad9361_dds_loopback(
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
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_slow_attack"], 1000000, 0.06, -20, 2000000, 0.12, -40,)],
)
def test_ad9361_two_tone_loopback(
    test_dds_two_tone,
    iio_uri,
    classname,
    channel,
    param_set,
    frequency1,
    scale1,
    peak_min1,
    frequency2,
    scale2,
    peak_min2,
):
    test_dds_two_tone(
        iio_uri,
        classname,
        channel,
        param_set,
        frequency1,
        scale1,
        peak_min1,
        frequency2,
        scale2,
        peak_min2,
    )
