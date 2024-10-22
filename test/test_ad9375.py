from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = ["ad9375", "adrv9375"]
classname = "adi.ad9375"

profile_path = dirname(realpath(__file__)) + "/ad9371_5_profiles/"
test_profiles = [join(profile_path, f) for f in listdir(profile_path)]


clgc_tracking_en_0 = {
    "tx_clgc_tracking_en_chan0": 1,
}

dpd_tracking_en_0 = {
    "tx_dpd_tracking_en_chan0": 1,
}

vswr_tracking_en_0 = {
    "tx_vswr_tracking_en_chan0": 1,
}

clgc_tracking_en_1 = {
    "tx_clgc_tracking_en_chan1": 1,
}

dpd_tracking_en_1 = {
    "tx_dpd_tracking_en_chan1": 1,
}

vswr_tracking_en_1 = {
    "tx_vswr_tracking_en_chan1": 1,
}


desired_gain_values = [-5, -4]


params = dict(
    one_cw_tone_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    one_cw_tone_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_attenuation_5dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-5,
        tx_hardwaregain_chan1=-5,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_attenuation_10dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-10,
        tx_hardwaregain_chan1=-10,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_attenuation_0dB_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_attenuation_20dB_auto=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="automatic",
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=-20,
        tx_hardwaregain_chan1=-20,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_rf_gain_0dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=0,
        rx_hardwaregain_chan1=0,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_rf_gain_20dB_manual=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=20,
        rx_hardwaregain_chan1=20,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=0,
        rx_temp_comp_gain_chan1=0,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
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
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=3,
        rx_temp_comp_gain_chan1=3,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
    ),
    change_temp_gain_down=dict(
        ensm_mode="radio_on",
        tx_lo=2500000000,
        rx_lo=2500000000,
        gain_control_mode="manual",
        rx_hardwaregain_chan0=10,
        rx_hardwaregain_chan1=10,
        rx_quadrature_tracking_en_chan0=1,
        rx_quadrature_tracking_en_chan1=1,
        rx_temp_comp_gain_chan0=-3,
        rx_temp_comp_gain_chan1=-3,
        tx_hardwaregain_chan0=0,
        tx_hardwaregain_chan1=0,
        tx_quadrature_tracking_en_chan0=1,
        tx_quadrature_tracking_en_chan1=1,
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
def test_ad9375_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_ad9375_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", range(2))
def test_ad9375_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
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
def test_ad9375_dds_loopback(
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
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency1, scale1, peak_min1, frequency2, scale2, peak_min2",
    [(params["one_cw_tone_auto"], 1000000, 0.06, -21, 2000000, 0.12, -15)],
)
def test_ad9375_two_tone_loopback(
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


########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, dds_scale, min_rssi, max_rssi",
    [
        (params["one_cw_tone_manual"], 0.5, 8.5, 10.5),
        (params["one_cw_tone_manual"], 0.12, 20.5, 23),
        (params["one_cw_tone_manual"], 0.25, 14.5, 16.5),
        (params["one_cw_tone_auto"], 0.12, 10.5, 13),
        (params["change_attenuation_5dB_manual"], 0.25, 19.5, 21.25),
        (params["change_attenuation_10dB_manual"], 0.25, 24.25, 26.25),
        (params["change_attenuation_0dB_auto"], 0.12, 2.25, 5.25),
        (params["change_attenuation_20dB_auto"], 0.12, 20.75, 22.75),
        (params["change_rf_gain_0dB_manual"], 0.25, 24.75, 26.75),
        (params["change_rf_gain_20dB_manual"], 0.25, 5, 6.5),
        (params["change_temp_gain_up"], 0.25, 14.5, 16.75),
        (params["change_temp_gain_down"], 0.25, 14.5, 16.75),
    ],
)
def test_ad9375_dds_gain_check_vary_power(
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
def test_ad9375_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "files", test_profiles,
)
def test_ad9375_profile_write(
    test_attribute_write_only_str, iio_uri, classname, attr, files
):
    test_attribute_write_only_str(iio_uri, classname, attr, files)


# AD9375 ONLY
########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, depends, values, tol, repeats",
    [
        ("tx_clgc_desired_gain_chan0", clgc_tracking_en_0, desired_gain_values, 0.5, 2),
        ("tx_clgc_desired_gain_chan1", clgc_tracking_en_1, desired_gain_values, 0.5, 2),
    ],
)
def test_ad9375_attr_with_depends(
    test_attribute_multiple_values_with_depends,
    iio_uri,
    classname,
    attr,
    depends,
    values,
    tol,
    repeats,
):
    test_attribute_multiple_values_with_depends(
        iio_uri, classname, attr, depends, values, tol, repeats
    )


########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, depends",
    [
        ("tx_clgc_current_gain_chan0", clgc_tracking_en_0),
        ("tx_clgc_current_gain_chan1", clgc_tracking_en_1),
        ("tx_clgc_orx_rms_chan0", clgc_tracking_en_0),
        ("tx_clgc_track_count_chan0", clgc_tracking_en_0),
        ("tx_clgc_track_count_chan1", clgc_tracking_en_1),
        ("tx_clgc_tx_gain_chan0", clgc_tracking_en_0),
        ("tx_clgc_tx_gain_chan1", clgc_tracking_en_1),
        ("tx_clgc_tx_rms_chan0", clgc_tracking_en_0),
        ("tx_clgc_tx_rms_chan1", clgc_tracking_en_1),
        ("tx_dpd_track_count_chan0", dpd_tracking_en_0),
        ("tx_dpd_track_count_chan1", dpd_tracking_en_1),
        ("tx_dpd_status_chan0", dpd_tracking_en_0),
        ("tx_dpd_status_chan1", dpd_tracking_en_1),
        ("tx_vswr_forward_gain_chan0", vswr_tracking_en_0),
        ("tx_vswr_forward_gain_chan1", vswr_tracking_en_1),
        ("tx_vswr_forward_gain_imag_chan0", vswr_tracking_en_0),
        ("tx_vswr_forward_gain_imag_chan1", vswr_tracking_en_1),
        ("tx_vswr_forward_gain_real_chan0", vswr_tracking_en_0),
        ("tx_vswr_forward_gain_real_chan1", vswr_tracking_en_1),
        ("tx_vswr_forward_orx_chan0", vswr_tracking_en_0),
        ("tx_vswr_forward_tx_chan0", vswr_tracking_en_0),
        ("tx_vswr_forward_tx_chan1", vswr_tracking_en_1),
        ("tx_vswr_reflected_gain_chan0", vswr_tracking_en_0),
        ("tx_vswr_reflected_gain_chan1", vswr_tracking_en_1),
        ("tx_vswr_reflected_gain_imag_chan0", vswr_tracking_en_0),
        ("tx_vswr_reflected_gain_imag_chan1", vswr_tracking_en_1),
        ("tx_vswr_reflected_gain_real_chan0", vswr_tracking_en_0),
        ("tx_vswr_reflected_gain_real_chan1", vswr_tracking_en_1),
        ("tx_vswr_reflected_orx_chan0", vswr_tracking_en_0),
        ("tx_vswr_reflected_tx_chan0", vswr_tracking_en_0),
        ("tx_vswr_reflected_tx_chan1", vswr_tracking_en_1),
        ("tx_vswr_track_count_chan0", vswr_tracking_en_0),
        ("tx_vswr_track_count_chan1", vswr_tracking_en_1),
    ],
)
def test_ad9375_attr_readonly_with_depends(
    test_attribute_readonly_with_depends, iio_uri, classname, attr, depends
):
    test_attribute_readonly_with_depends(iio_uri, classname, attr, depends)


########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, depends, start, stop",
    [
        ("tx_dpd_model_error_chan0", dpd_tracking_en_0, 0, 100),
        ("tx_dpd_model_error_chan1", dpd_tracking_en_1, 0, 100),
    ],
)
def test_ad9375_attr_range_readonly(
    test_attribute_check_range_readonly_with_depends,
    iio_uri,
    classname,
    attr,
    depends,
    start,
    stop,
):
    test_attribute_check_range_readonly_with_depends(
        iio_uri, classname, attr, depends, start, stop
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("tx_clgc_tracking_en_chan0", 1),
        ("tx_clgc_tracking_en_chan0", 0),
        ("tx_clgc_tracking_en_chan1", 1),
        ("tx_clgc_tracking_en_chan1", 0),
        ("tx_dpd_actuator_en_chan0", 1),
        ("tx_dpd_actuator_en_chan0", 0),
        ("tx_dpd_actuator_en_chan1", 1),
        ("tx_dpd_actuator_en_chan1", 0),
        ("tx_vswr_tracking_en_chan0", 1),
        ("tx_vswr_tracking_en_chan0", 0),
        ("tx_vswr_tracking_en_chan1", 1),
        ("tx_vswr_tracking_en_chan1", 0),
        ("tx_dpd_tracking_en_chan0", 1),
        ("tx_dpd_tracking_en_chan0", 0),
        ("tx_dpd_tracking_en_chan1", 1),
        ("tx_dpd_tracking_en_chan1", 0),
    ],
)
def test_ad9375_attr_boolean(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value", [("tx_dpd_reset_en_chan0", 1), ("tx_dpd_reset_en_chan1", 1),],
)
def test_ad9375_attr_write_only(
    test_attribute_write_only_str, iio_uri, classname, attr, value
):
    test_attribute_write_only_str(iio_uri, classname, attr, value)
