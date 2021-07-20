from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = ["adrv9002-rx1tx1", "adrv9002-rx2tx2"]
classname = "adi.adrv9002"
profile_path = dirname(realpath(__file__)) + "/adrv9002_profiles/"
nco_test_profile = profile_path + "lte_10_lvds_nco_api_48_8_7.json"
nco_test_stream = profile_path + "lte_10_lvds_nco_api_48_8_7.stream"
lte_20_lvds_profile = profile_path + "lte_20_lvds_api_48_8_7.json"
lte_20_lvds_stream = profile_path + "lte_20_lvds_api_48_8_7.stream"
lte_40_lvds_profile = profile_path + "lte_40_lvds_api_48_8_7.json"
lte_40_lvds_stream = profile_path + "lte_40_lvds_api_48_8_7.stream"
lte_5_cmos_profile = profile_path + "lte_5_cmos_api_48_8_7.json"
lte_5_cmos_stream = profile_path + "lte_5_cmos_api_48_8_7.stream"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("rx_hardwaregain_chan0", 0, 34, 0.5, 0),
        ("rx_hardwaregain_chan1", 0, 34, 0.5, 0),
        ("tx_hardwaregain_chan0", -40, 0.0, 0.05, 0),
        ("tx_hardwaregain_chan1", -40, 0.0, 0.05, 0),
        ("tx0_lo", 30000000, 6000000000, 1, 8),
        ("tx1_lo", 30000000, 6000000000, 1, 8),
        ("rx0_lo", 30000000, 6000000000, 1, 8),
        ("rx1_lo", 30000000, 6000000000, 1, 8),
    ],
)
def test_adrv9002_float_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("agc_tracking_en_chan0", [0, 1]),
        ("bbdc_rejection_tracking_en_chan0", [0, 1]),
        ("hd_tracking_en_chan0", [0, 1]),
        ("quadrature_fic_tracking_en_chan0", [0, 1]),
        ("quadrature_w_poly_tracking_en_chan0", [0, 1]),
        ("rfdc_tracking_en_chan0", [0, 1]),
        ("rssi_tracking_en_chan0", [0, 1]),
        ("agc_tracking_en_chan1", [0, 1]),
        ("bbdc_rejection_tracking_en_chan1", [0, 1]),
        ("hd_tracking_en_chan1", [0, 1]),
        ("quadrature_fic_tracking_en_chan1", [0, 1]),
        ("quadrature_w_poly_tracking_en_chan1", [0, 1]),
        ("rfdc_tracking_en_chan1", [0, 1]),
        ("rssi_tracking_en_chan1", [0, 1]),
        ("close_loop_gain_tracking_en_chan0", [0, 1]),
        ("lo_leakage_tracking_en_chan0", [0, 1]),
        ("loopback_delay_tracking_en_chan0", [0, 1]),
        ("pa_correction_tracking_en_chan0", [0, 1]),
        ("quadrature_tracking_en_chan0", [0, 1]),
        ("close_loop_gain_tracking_en_chan1", [0, 1]),
        ("lo_leakage_tracking_en_chan1", [0, 1]),
        ("loopback_delay_tracking_en_chan1", [0, 1]),
        ("pa_correction_tracking_en_chan1", [0, 1]),
        ("quadrature_tracking_en_chan1", [0, 1]),
        ("tx0_en", [0, 1]),
        ("tx1_en", [0, 1]),
        ("rx1_en", [0, 1]),
        ("rx0_en", [0, 1]),
    ],
)
def test_adrv9002_boolean_attr(
    test_attribute_multipe_values, iio_uri, classname, attr, val
):
    test_attribute_multipe_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("rx0_port_en", ["pin", "spi"]),
        ("rx1_port_en", ["pin", "spi"]),
        ("tx0_port_en", ["pin", "spi"]),
        ("tx1_port_en", ["pin", "spi"]),
        ("tx_ensm_mode_chan0", ["calibrated", "primed", "rf_enabled"]),
        ("tx_ensm_mode_chan1", ["calibrated", "primed", "rf_enabled"]),
        ("rx_ensm_mode_chan0", ["calibrated", "primed", "rf_enabled"]),
        ("rx_ensm_mode_chan1", ["calibrated", "primed", "rf_enabled"]),
        (
            "digital_gain_control_mode_chan0",
            [
                "Gain_Correction_manual_control",
                "Gain_Compensation_manual_control",
                "Gain_Correction_automatic_control",
                "Gain_Compensation_automatic_control",
            ],
        ),
        (
            "digital_gain_control_mode_chan1",
            [
                "Gain_Correction_manual_control",
                "Gain_Compensation_manual_control",
                "Gain_Correction_automatic_control",
                "Gain_Compensation_automatic_control",
            ],
        ),
        ("gain_control_mode_chan0", ["pin", "automatic", "spi"]),
        ("gain_control_mode_chan1", ["pin", "automatic", "spi"]),
        ("atten_control_mode_chan0", ["bypass", "pin", "spi"]),
        ("atten_control_mode_chan1", ["bypass", "pin", "spi"]),
    ],
)
def test_adrv9002_str_attr(
    test_attribute_multipe_values, iio_uri, classname, attr, val
):
    test_attribute_multipe_values(iio_uri, classname, attr, val, 0)


#########################################
# baseband rx sample rate should be > 1MHz to run this test


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val, depends",
    [
        (
            "interface_gain_chan0",
            ["-36dB", "-30dB", "-24dB", "-18dB", "-12dB", "-6dB", "0dB"],
            dict(
                digital_gain_control_mode_chan0="Gain_Compensation_manual_control",
                rx_ensm_mode_chan0="rf_enabled",
            ),
        ),
        (
            "interface_gain_chan1",
            ["-36dB", "-30dB", "-24dB", "-18dB", "-12dB", "-6dB", "0dB"],
            dict(
                digital_gain_control_mode_chan1="Gain_Compensation_manual_control",
                rx_ensm_mode_chan1="rf_enabled",
            ),
        ),
    ],
)
def test_adrv9002_interface_gain_wideband(
    test_attribute_multipe_values_with_depends, iio_uri, classname, attr, depends, val
):
    test_attribute_multipe_values_with_depends(
        iio_uri, classname, attr, depends, val, 0
    )


#########################################
# baseband rx sample rate should be < 1MHz to run this test


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val, depends",
    [
        (
            "interface_gain_chan0",
            [
                "-36dB",
                "-30dB",
                "-24dB",
                "-18dB",
                "-12dB",
                "-6dB",
                "0dB",
                "6dB",
                "12dB",
                "18dB",
            ],
            dict(
                digital_gain_control_mode_chan0="Gain_Compensation_manual_control",
                rx_ensm_mode_chan0="rf_enabled",
            ),
        ),
        (
            "interface_gain_chan1",
            [
                "-36dB",
                "-30dB",
                "-24dB",
                "-18dB",
                "-12dB",
                "-6dB",
                "0dB",
                "6dB",
                "12dB",
                "18dB",
            ],
            dict(
                digital_gain_control_mode_chan0="Gain_Compensation_manual_control",
                rx_ensm_mode_chan0="rf_enabled",
            ),
        ),
        (
            "interface_gain_chan0",
            ["0dB", "6dB", "12dB", "18dB"],
            dict(
                digital_gain_control_mode_chan0="Gain_Correction_manual_control",
                rx_ensm_mode_chan0="rf_enabled",
            ),
        ),
        (
            "interface_gain_chan1",
            ["0dB", "6dB", "12dB", "18dB"],
            dict(
                digital_gain_control_mode_chan0="Gain_Correction_manual_control",
                rx_ensm_mode_chan0="rf_enabled",
            ),
        ),
    ],
)
def test_adrv9002_interface_gain_narrowband(
    test_attribute_multipe_values_with_depends, iio_uri, classname, attr, depends, val
):
    test_attribute_multipe_values_with_depends(
        iio_uri, classname, attr, depends, val, 0
    )


#########################################
@pytest.mark.lvds_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "profile_file, depends",
    [
        (lte_40_lvds_profile, {"write_stream": lte_40_lvds_stream}),
        (lte_20_lvds_profile, {"write_stream": lte_20_lvds_stream}),
    ],
)
def test_adrv9002_profile_write(
    test_attribute_write_only_str_with_depends,
    iio_uri,
    classname,
    attr,
    profile_file,
    depends,
):
    test_attribute_write_only_str_with_depends(
        iio_uri, classname, attr, profile_file, depends
    )


#########################################
@pytest.mark.lvds_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "profile_file, depends", [(nco_test_profile, {"write_stream": nco_test_stream})]
)
def test_adrv9002_nco_write_profile(
    test_attribute_write_only_str_with_depends,
    iio_uri,
    classname,
    attr,
    profile_file,
    depends,
):
    test_attribute_write_only_str_with_depends(
        iio_uri, classname, attr, profile_file, depends
    )


#########################################
@pytest.mark.cmos_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "profile_file, depends", [(lte_5_cmos_profile, {"write_stream": lte_5_cmos_stream})]
)
def test_adrv9002_stream_profile_write(
    test_attribute_write_only_str_with_depends,
    iio_uri,
    classname,
    attr,
    profile_file,
    depends,
):
    test_attribute_write_only_str_with_depends(
        iio_uri, classname, attr, profile_file, depends
    )


#########################################
@pytest.mark.cmos_test
@pytest.mark.iio_hardware(hardware)
def test_adrv9002_stream_profile_write_both(iio_uri):
    import adi

    sdr = adi.adrv9002(iio_uri)
    sdr.write_stream_profile(lte_5_cmos_stream, lte_5_cmos_profile)


#########################################
# It depends on test_adrv9002_nco_write_profile to be run first.
# Maybe we should think in adding something like pytest-dependency
@pytest.mark.lvds_test
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("rx0_nco_frequency", -20000, 20000, 1, 0),
        ("rx1_nco_frequency", -20000, 20000, 1, 0),
        ("tx0_nco_frequency", -20000, 20000, 1, 0),
        ("tx1_nco_frequency", -20000, 20000, 1, 0),
    ],
)
def test_adrv9002_nco(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware[0])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_adrv9002_tx_data_rx1tx1(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware[1])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("use_tx2", [True])
def test_adrv9002_tx_data_rx2tx2(test_dma_tx, iio_uri, classname, channel, use_tx2):
    test_dma_tx(iio_uri, classname, channel, use_tx2)


#########################################
@pytest.mark.iio_hardware(hardware[0])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_adrv9002_rx_data_rx1tx1(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware[1])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("use_rx2", [True])
def test_adrv9002_rx_data_rx2tx2(test_dma_rx, iio_uri, classname, channel, use_rx2):
    test_dma_rx(iio_uri, classname, channel, use_rx2)


########################################
@pytest.mark.iio_hardware(hardware[0])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx0_lo=1000000000,
            rx0_lo=1000000000,
            tx1_lo=1000000000,
            rx1_lo=1000000000,
            rx_ensm_mode_chan0="rf_enabled",
            rx_ensm_mode_chan1="rf_enabled",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_ensm_mode_chan0="rf_enabled",
            tx_ensm_mode_chan1="rf_enabled",
        )
    ],
)
def test_adrv9002_cw_loopback(test_cw_loopback, iio_uri, classname, channel, param_set):
    test_cw_loopback(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware[1])
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx0_lo=1000000000,
            rx0_lo=1000000000,
            tx1_lo=1000000000,
            rx1_lo=1000000000,
            rx_ensm_mode_chan0="rf_enabled",
            rx_ensm_mode_chan1="rf_enabled",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_ensm_mode_chan0="rf_enabled",
            tx_ensm_mode_chan1="rf_enabled",
        )
    ],
)
@pytest.mark.parametrize("use_tx2rx2", [False, True])
def test_adrv9002_cw_loopback_split_dma(
    test_cw_loopback, iio_uri, classname, channel, param_set, use_tx2rx2
):
    test_cw_loopback(iio_uri, classname, channel, param_set, use_tx2rx2, use_tx2rx2)
