from os import listdir
from os.path import dirname, join, realpath

import pytest

import adi.jesd as jesd
skip_jesd = jesd is None

hardware = ["adrv9025"]
classname = "adi.adrv9025"

# profile_path = dirname(realpath(__file__)) + "/adrv9025_profiles/"
# test_profiles = [join(profile_path, f) for f in listdir(profile_path)]

params = dict(
    one_cw_tone_manual=dict(
        trx_lo=2500000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    one_cw_tone_slow_attack=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_attenuation_5dB_manual=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=-5,
        tx_hardwaregain_chan1=-5,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_attenuation_10dB_manual=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_attenuation_0dB_slow_attack=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_attenuation_20dB_slow_attack=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=-20,
        tx_hardwaregain_chan1=-20,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_rf_gain_0dB_manual=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_rf_gain_20dB_manual=dict(
        ensm_mode="radio_on",
        trx_lo=2500000000,
        gain_control_mode_chan0="manual",
        gain_control_mode_chan1="manual",
        obs_powerdown_en=1,
        rx_powerdown_en_chan0=0,
        rx_powerdown_en_chan1=0,
        rx_hardwaregain_chan0=20,
        rx_hardwaregain_chan1=20,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_trx_lo_1GHz_slow_attack=dict(
        trx_lo=1000000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_trx_lo_3GHz_slow_attack=dict(
        trx_lo=3000000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
    change_trx_lo_5GHz_slow_attack=dict(
        trx_lo=5000000000,
        gain_control_mode_chan0="slow_attack",
        gain_control_mode_chan1="slow_attack",
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        calibrate_rx_qec_en=1,
        calibrate_tx_qec_en=1,
        calibrate=1,
    ),
)

# params_obs = dict(
#     obs_tx=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_TX_LO",
#         obs_hardwaregain=0,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_tx_change_attenuation_10dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=-10,
#         tx_hardwaregain_chan1=-10,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_TX_LO",
#         obs_hardwaregain=0,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_tx_change_rf_gain_10dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_TX_LO",
#         obs_hardwaregain=10,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_tx_change_rf_gain_5dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_TX_LO",
#         obs_hardwaregain=5,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_aux=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_AUX_LO",
#         obs_hardwaregain=0,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_aux_change_attenuation_10dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=-10,
#         tx_hardwaregain_chan1=-10,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_AUX_LO",
#         obs_hardwaregain=0,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_aux_change_rf_gain_10dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_AUX_LO",
#         obs_hardwaregain=10,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
#     obs_aux_change_rf_gain_5dB=dict(
#         ensm_mode="radio_on",
#         trx_lo=2500000000,
#         rx_powerdown_en_chan0=1,
#         rx_powerdown_en_chan1=1,
#         obs_powerdown_en=0,
#         tx_hardwaregain_chan0=0,
#         tx_hardwaregain_chan1=0,
#         tx_quadrature_tracking_en_chan0=1,
#         tx_quadrature_tracking_en_chan1=1,
#         aux_obs_lo=2500000000,
#         obs_quadrature_tracking_en=1,
#         obs_rf_port_select="OBS_AUX_LO",
#         obs_hardwaregain=5,
#         calibrate_rx_qec_en=1,
#         calibrate_tx_qec_en=1,
#         calibrate=1,
#     ),
# )


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
def test_adrv9025_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_adrv9025_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min",
    [
        (params["one_cw_tone_manual"], 2000000, 0.5, -42),
        (params["one_cw_tone_manual"], 2000000, 0.12, -55),
        (params["one_cw_tone_manual"], 2000000, 0.25, -48),
        (params["one_cw_tone_slow_attack"], 1000000, 0.12, -44),
        (params["one_cw_tone_slow_attack"], 2000000, 0.12, -44),
        (params["one_cw_tone_slow_attack"], 500000, 0.12, -44),
        (params["change_attenuation_5dB_manual"], 2000000, 0.25, -53),
        (params["change_attenuation_10dB_manual"], 2000000, 0.25, -58),
        (params["change_attenuation_0dB_slow_attack"], 1000000, 0.12, -35),
        (params["change_attenuation_20dB_slow_attack"], 1000000, 0.12, -54),
        (params["change_rf_gain_0dB_manual"], 2000000, 0.25, -59),
        (params["change_rf_gain_20dB_manual"], 2000000, 0.25, -38),
    ],
)
def test_adrv9025_dds_loopback(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale",
    [
        (params["one_cw_tone_manual"], 2000000, 0.5),
        (params["one_cw_tone_manual"], 2000000, 0.12),
        (params["one_cw_tone_manual"], 2000000, 0.25),
        (params["one_cw_tone_slow_attack"], 1000000, 0.12),
        (params["one_cw_tone_slow_attack"], 2000000, 0.12),
        (params["one_cw_tone_slow_attack"], 500000, 0.12),
        (params["change_attenuation_5dB_manual"], 2000000, 0.25),
        (params["change_attenuation_10dB_manual"], 2000000, 0.25),
        (params["change_attenuation_0dB_slow_attack"], 1000000, 0.12),
        (params["change_attenuation_20dB_slow_attack"], 1000000, 0.12),
        (params["change_rf_gain_0dB_manual"], 2000000, 0.25),
        (params["change_rf_gain_20dB_manual"], 2000000, 0.25),
    ],
)
@pytest.mark.parametrize("peak_min", [-50])
def test_adrv9025_dds_loopback_with_10dB_splitter(
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
# @pytest.mark.obs_required
# @pytest.mark.iio_hardware(hardware)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize(
#     "channel, param_set",
#     [
#         (0, params_obs["obs_tx"]),
#         (0, params_obs["obs_tx_change_attenuation_10dB"]),
#         (0, params_obs["obs_tx_change_rf_gain_10dB"]),
#         (0, params_obs["obs_tx_change_rf_gain_5dB"]),
#         (0, params_obs["obs_aux"]),
#         (0, params_obs["obs_aux_change_attenuation_10dB"]),
#         (0, params_obs["obs_aux_change_rf_gain_10dB"]),
#         (0, params_obs["obs_aux_change_rf_gain_5dB"]),
#     ],
# )
# @pytest.mark.parametrize(
#     "frequency, scale, peak_min, use_obs", [(50000000, 0.25, -40.5, True)]
# )
# def test_adrv9025_dds_loopback_for_obs(
#     test_dds_loopback,
#     iio_uri,
#     classname,
#     param_set,
#     channel,
#     frequency,
#     scale,
#     peak_min,
#     use_obs,
# ):
#     test_dds_loopback(
#         iio_uri, classname, param_set, channel, frequency, scale, peak_min, use_obs
#     )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_slow_attack"], 1000000, 0.06, -21, 2000000, 0.12, -15)],
)
def test_adrv9025_two_tone_loopback(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_slow_attack"], 1000000, 0.06, -41, 2000000, 0.12, -35)],
)
def test_adrv9025_two_tone_loopback_with_10dB_splitter(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        params["one_cw_tone_manual"],
        params["one_cw_tone_slow_attack"],
        params["change_attenuation_5dB_manual"],
        params["change_attenuation_10dB_manual"],
        params["change_attenuation_0dB_slow_attack"],
        params["change_attenuation_20dB_slow_attack"],
        params["change_rf_gain_0dB_manual"],
        params["change_rf_gain_20dB_manual"],
        params["change_trx_lo_1GHz_slow_attack"],
        params["change_trx_lo_3GHz_slow_attack"],
        params["change_trx_lo_5GHz_slow_attack"],
    ],
)
@pytest.mark.parametrize("sfdr_min", [30])
def test_adrv9025_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        params["one_cw_tone_manual"],
        params["one_cw_tone_slow_attack"],
        params["change_attenuation_5dB_manual"],
        params["change_attenuation_10dB_manual"],
        params["change_attenuation_0dB_slow_attack"],
        params["change_attenuation_20dB_slow_attack"],
        params["change_rf_gain_0dB_manual"],
        params["change_rf_gain_20dB_manual"],
        params["change_trx_lo_1GHz_slow_attack"],
        params["change_trx_lo_3GHz_slow_attack"],
        params["change_trx_lo_5GHz_slow_attack"],
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_adrv9025_sfdr_with_10dB_splitter(
    test_sfdr, iio_uri, classname, channel, param_set, sfdr_min
):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
# @pytest.mark.obs_required
# @pytest.mark.iio_hardware(hardware)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize("channel", [0, 1])
# @pytest.mark.parametrize(
#     "param_set",
#     [
#         params_obs["obs_tx"],
#         params_obs["obs_tx_change_attenuation_10dB"],
#         params_obs["obs_tx_change_rf_gain_10dB"],
#         params_obs["obs_tx_change_rf_gain_5dB"],
#         params_obs["obs_aux"],
#         params_obs["obs_aux_change_attenuation_10dB"],
#         params_obs["obs_aux_change_rf_gain_10dB"],
#         params_obs["obs_aux_change_rf_gain_5dB"],
#     ],
# )
# @pytest.mark.parametrize("sfdr_min", [45])
# @pytest.mark.parametrize("use_obs", [True])
# def test_adrv9025_sfdr_for_obs(
#     test_sfdr, iio_uri, classname, channel, param_set, sfdr_min, use_obs
# ):
#     test_sfdr(iio_uri, classname, channel, param_set, sfdr_min, use_obs)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_slow_attack"], 0.12, 33.5, 41.5),
        (params["change_attenuation_0dB_slow_attack"], 0.12, 24, 32),
        (params["change_attenuation_20dB_slow_attack"], 0.12, 40, 45.5),
        (params["change_trx_lo_1GHz_slow_attack"], 0, 35, 60),
        (params["change_trx_lo_1GHz_slow_attack"], 0.9, 25, 35),
        (params["change_trx_lo_3GHz_slow_attack"], 0, 35, 60),
        (params["change_trx_lo_3GHz_slow_attack"], 0.9, 0, 22),
        (params["change_trx_lo_5GHz_slow_attack"], 0, 35, 60),
        (params["change_trx_lo_5GHz_slow_attack"], 0.9, 20, 25),
    ],
)
def test_adrv9025_dds_gain_check_agc(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi",
    [
        (params["one_cw_tone_slow_attack"], 0.12, 40),
        (params["change_attenuation_0dB_slow_attack"], 0.12, 30),
        (params["change_attenuation_20dB_slow_attack"], 0.12, 43.5),
        (params["change_trx_lo_1GHz_slow_attack"], 0, 43.5),
        (params["change_trx_lo_1GHz_slow_attack"], 0.9, 30),
        (params["change_trx_lo_3GHz_slow_attack"], 0, 43.75),
        (params["change_trx_lo_3GHz_slow_attack"], 0.9, 23),
        (params["change_trx_lo_5GHz_slow_attack"], 0, 43.75),
        (params["change_trx_lo_5GHz_slow_attack"], 0.9, 25),
    ],
)
@pytest.mark.parametrize("max_rssi", [50])
def test_adrv9025_dds_gain_check_agc_with_10db_splitter(
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
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_manual"], 0.5, 30, 40),
        (params["one_cw_tone_manual"], 0.12, 40, 45),
        (params["one_cw_tone_manual"], 0.25, 35, 45),
        (params["change_attenuation_5dB_manual"], 0.25, 40, 45),
        (params["change_attenuation_10dB_manual"], 0.25, 40, 45),
        (params["change_rf_gain_0dB_manual"], 0.25, 40, 45),
        (params["change_rf_gain_20dB_manual"], 0.25, 25, 35),
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
            30,
            45,
        ),
    ],
)
def test_adrv9025_dds_gain_check_vary_power(
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_manual"], 0.5, 38, 45),
        (params["one_cw_tone_manual"], 0.12, 43, 45),
        (params["one_cw_tone_manual"], 0.25, 43, 45),
        (params["change_attenuation_5dB_manual"], 0.25, 43, 45),
        (params["change_attenuation_10dB_manual"], 0.25, 43, 45),
        (params["change_rf_gain_0dB_manual"], 0.25, 42.5, 44.5),
        (params["change_rf_gain_20dB_manual"], 0.25, 34, 44),
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
            42.5,
            44.5,
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
            36,
            43.5,
        ),
    ],
)
def test_adrv9025_dds_gain_check_vary_power_with_10dB_splitter(
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
# TODO: Test, see what's its difference with dds_loopback, PROBLEMATIC
# OSError: [Errno 5] Input/output error
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
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
def test_adrv9025_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


#########################################
# @pytest.mark.iio_hardware(hardware)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize("attr", ["profile"])
# @pytest.mark.parametrize(
#     "files", test_profiles,
# )
# def test_adrv9025_profile_write(
#     test_attribute_write_only_str, iio_uri, classname, attr, files
# ):
#     test_attribute_write_only_str(iio_uri, classname, attr, files)


#########################################
@pytest.mark.skipif(skip_jesd, reason="JESD module not importable")
@pytest.mark.iio_hardware(hardware)
def test_adrv9025_jesd(iio_uri):
    import adi

    sdr = adi.adrv9025(uri=iio_uri, jesd_monitor=True)
    info = sdr._jesd.get_all_statuses()
    assert info
