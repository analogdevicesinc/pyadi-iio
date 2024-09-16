from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = ["ad9371", "adrv9371"]
classname = "adi.ad9371"

profile_path = dirname(realpath(__file__)) + "/ad9371_5_profiles/"
test_profiles = [join(profile_path, f) for f in listdir(profile_path)]

# use 6in sma cables
# for obs setup, add only splitter to TX1->RX1/ORX1

params = dict(
    one_cw_tone_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    one_cw_tone_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_attenuation_5dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-5,
        tx_hardwaregain_chan1=-5,
    ),
    change_attenuation_10dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
    ),
    change_attenuation_0dB_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    change_attenuation_20dB_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-20,
        tx_hardwaregain_chan1=-20,
    ),
    change_rf_gain_0dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    change_rf_gain_20dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=20,
        rx_hardwaregain_chan1=20,
    ),
    change_rf_gain_10dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
    ),
    change_temp_gain_up=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_temp_comp_gain_chan0=3,
        rx_temp_comp_gain_chan1=3,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
    change_temp_gain_down=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_temp_comp_gain_chan0=-3,
        rx_temp_comp_gain_chan1=-3,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
    ),
)

params_obs = dict(
    obs_orx1_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_TX_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=0,
    ),
    obs_orx1_change_attenuation_10dB=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_TX_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=0,
    ),
    obs_orx1_change_rf_gain_20dB=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_TX_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=20,
        obs_temp_comp_gain=0,
    ),
    obs_orx1_change_temp_gain_up=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_TX_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=3,
    ),
    obs_orx1_change_temp_gain_down=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_TX_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=-3,
    ),
    snf_orx1_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_SN_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=0,
    ),
    snf_orx1_change_attenuation_10dB=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_SN_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=30,
        obs_temp_comp_gain=0,
    ),
    snf_orx1_change_rf_gain_20dB=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        sn_lo=2500000000,
        obs_quadrature_tracking_en=1,
        obs_rf_port_select="ORX1_SN_LO",
        obs_gain_control_mode="manual",
        obs_hardwaregain=20,
        obs_temp_comp_gain=0,
    ),
)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1", -41.95, 0.0, 0.05, 0.05),
        ("tx_lo", 70000000, 6000000000, 1000, 0),
        ("rx_lo", 70000000, 6000000000, 1000, 0),
    ],
)
def test_ad9371_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_ad9371_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.no_obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min",
    [
        (params["one_cw_tone_manual"], 2000000, 0.5, -13),
        (params["one_cw_tone_manual"], 2000000, 0.12, -25),
        (params["one_cw_tone_manual"], 2000000, 0.25, -19),
        (params["one_cw_tone_auto"], 1000000, 0.12, -14.7),
        (params["one_cw_tone_auto"], 2000000, 0.12, -14.7),
        (params["one_cw_tone_auto"], 500000, 0.12, -14.7),
        (params["change_attenuation_5dB_manual"], 2000000, 0.25, -23.8),
        (params["change_attenuation_10dB_manual"], 2000000, 0.25, -28.75),
        (params["change_attenuation_0dB_auto"], 1000000, 0.12, -9),
        (params["change_attenuation_20dB_auto"], 1000000, 0.12, -24.7),
        (params["change_rf_gain_0dB_manual"], 2000000, 0.25, -29),
        (params["change_rf_gain_20dB_manual"], 2000000, 0.25, -9),
        (params["change_temp_gain_up"], 2000000, 0.25, -16),
        (params["change_temp_gain_down"], 2000000, 0.25, -22),
    ],
)
def test_ad9371_dds_loopback(
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


########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min",
    [
        (params["one_cw_tone_manual"], 2000000, 0.5, -33),
        (params["one_cw_tone_manual"], 2000000, 0.12, -45),
        (params["one_cw_tone_manual"], 2000000, 0.25, -39),
        (params["one_cw_tone_auto"], 1000000, 0.12, -34.7),
        (params["one_cw_tone_auto"], 2000000, 0.12, -34.7),
        (params["one_cw_tone_auto"], 500000, 0.12, -34.7),
        (params["change_attenuation_5dB_manual"], 2000000, 0.25, -43.8),
        (params["change_attenuation_10dB_manual"], 2000000, 0.25, -48.75),
        (params["change_attenuation_0dB_auto"], 1000000, 0.12, -29),
        (params["change_attenuation_20dB_auto"], 1000000, 0.12, -44.7),
        (params["change_rf_gain_0dB_manual"], 2000000, 0.25, -49),
        (params["change_rf_gain_20dB_manual"], 2000000, 0.25, -29),
        (params["change_temp_gain_up"], 2000000, 0.25, -36),
        (params["change_temp_gain_down"], 2000000, 0.25, -42),
    ],
)
def test_ad9371_dds_loopback_with_10dB_splitter(
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


########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, param_set",
    [
        (0, params_obs["obs_orx1_manual"]),
        (0, params_obs["obs_orx1_change_rf_gain_20dB"]),
        (0, params_obs["obs_orx1_change_temp_gain_up"]),
        (0, params_obs["obs_orx1_change_temp_gain_down"]),
        (0, params_obs["snf_orx1_manual"]),
        (0, params_obs["snf_orx1_change_rf_gain_20dB"]),
    ],
)
@pytest.mark.parametrize(
    "frequency, scale, peak_min, use_obs", [(5000000, 0.25, -52.5, True)]
)
def test_ad9371_dds_loopback_for_obs(
    test_dds_loopback,
    iio_uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
    use_obs,
):
    test_dds_loopback(
        iio_uri, classname, param_set, channel, frequency, scale, peak_min, use_obs
    )


#########################################
@pytest.mark.no_obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_auto"], 1000000, 0.06, -21, 2000000, 0.12, -15)],
)
def test_ad9371_two_tone_loopback(
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


#########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_auto"], 1000000, 0.06, -41, 2000000, 0.12, -35)],
)
def test_ad9371_two_tone_loopback_with_10dB_splitter(
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


#########################################
@pytest.mark.no_obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_manual"], 0.5, 8.5, 10.5),
        (params["one_cw_tone_manual"], 0.12, 20.5, 22.5),
        (params["one_cw_tone_manual"], 0.25, 14.5, 16.5),
        (params["one_cw_tone_auto"], 0.12, 10.5, 13.5),
        (params["change_attenuation_5dB_manual"], 0.25, 19.5, 22.5),
        (params["change_attenuation_10dB_manual"], 0.25, 24.25, 26.25),
        (params["change_attenuation_0dB_auto"], 0.12, 2.5, 5.5),
        (params["change_attenuation_20dB_auto"], 0.12, 20.75, 23.75),
        (params["change_rf_gain_0dB_manual"], 0.25, 24.75, 26.75),
        (params["change_rf_gain_20dB_manual"], 0.25, 5, 7),
        (params["change_temp_gain_up"], 0.25, 14.5, 16.5),
        (params["change_temp_gain_down"], 0.25, 14.5, 16.5),
    ],
)
def test_ad9371_dds_gain_check_vary_power(
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
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, param_set, dds_scale, min_rssi, max_rssi",
    [
        (0, params["one_cw_tone_manual"], 0.5, 18, 20.75),
        (1, params["one_cw_tone_manual"], 0.5, 8, 10.75),
        (0, params["one_cw_tone_auto"], 0.12, 21, 23.25),
        (1, params["one_cw_tone_auto"], 0.12, 11, 13.25),
        (0, params["change_attenuation_5dB_manual"], 0.25, 29, 31.25),
        (1, params["change_attenuation_5dB_manual"], 0.25, 19, 21.5),
        (0, params["change_attenuation_0dB_auto"], 0.12, 11, 13.5),
        (1, params["change_attenuation_0dB_auto"], 0.12, 2, 5.5),
        (0, params["change_rf_gain_0dB_manual"], 0.25, 34, 36.5),
        (1, params["change_rf_gain_0dB_manual"], 0.25, 24, 26.5),
        (0, params["change_temp_gain_up"], 0.25, 24, 26.5),
        (1, params["change_temp_gain_up"], 0.25, 14, 16.5),
    ],
)
def test_ad9371_dds_gain_check_vary_power_with_10dB_splitter(
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
@pytest.mark.no_obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        params["one_cw_tone_manual"],
        params["one_cw_tone_auto"],
        params["change_attenuation_5dB_manual"],
        params["change_attenuation_10dB_manual"],
        params["change_attenuation_0dB_auto"],
        params["change_attenuation_20dB_auto"],
        params["change_rf_gain_0dB_manual"],
        params["change_rf_gain_10dB_manual"],
        params["change_temp_gain_up"],
        params["change_temp_gain_down"],
    ],
)
@pytest.mark.parametrize("sfdr_min", [45])
def test_ad9371_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        params["one_cw_tone_manual"],
        params["one_cw_tone_auto"],
        params["change_attenuation_5dB_manual"],
        params["change_attenuation_10dB_manual"],
        params["change_attenuation_0dB_auto"],
        params["change_attenuation_20dB_auto"],
        params["change_rf_gain_0dB_manual"],
        params["change_rf_gain_10dB_manual"],
        params["change_temp_gain_up"],
        params["change_temp_gain_down"],
    ],
)
@pytest.mark.parametrize("sfdr_min", [45])
def test_ad9371_sfdr_with_10dB_splitter(
    test_sfdr, iio_uri, classname, channel, param_set, sfdr_min
):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, param_set, sfdr_min",
    [
        (0, params_obs["obs_orx1_change_attenuation_10dB"], 30),
        (0, params_obs["snf_orx1_change_attenuation_10dB"], 30),
    ],
)
@pytest.mark.parametrize("use_obs", [True])
def test_ad9371_sfdr_for_obs(
    test_sfdr, iio_uri, classname, channel, param_set, sfdr_min, use_obs
):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min, use_obs)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "files", test_profiles,
)
def test_ad9371_profile_write(
    test_attribute_write_only_str, iio_uri, classname, attr, files
):
    test_attribute_write_only_str(iio_uri, classname, attr, files)
