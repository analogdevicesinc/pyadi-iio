from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = "adrv9002"
classname = "adi.adrv9002"
profile_path = dirname(realpath(__file__)) + "/adrv9002_profiles/"
nco_test_profile = profile_path + "FDD_9MHz_2rx_2tx_LO_2_4G_NCO.json"
lvds_test_profiles = [
    profile_path + "FDD_20MHz_2rx_2tx_LO_2_4G.json",
    profile_path + "FDD_40MHz_2rx_2tx_LO_2_4G.json",
]
lte_14_profile = profile_path + "lte_1_4_cmos_fdd_api_29_2_9.json"
lte_14_stream = profile_path + "lte_1_4_cmos_fdd_api_29_2_9.stream"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("rx_hardwaregain_chan0", 0, 30, 0.5, 0),
        ("rx_hardwaregain_chan1", 0, 30, 0.5, 0),
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "files", lvds_test_profiles,
)
def test_adrv9002_profile_write(
    test_attribute_write_only_str, iio_uri, classname, attr, files
):
    test_attribute_write_only_str(iio_uri, classname, attr, files)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, file", [("profile", nco_test_profile),],
)
def test_adrv9002_nco_write_profile(
    test_attribute_write_only_str, iio_uri, classname, attr, file
):
    test_attribute_write_only_str(iio_uri, classname, hardware, attr, file)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "profile_file, depends", [(lte_14_profile, {"write_stream": lte_14_stream})]
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
@pytest.mark.iio_hardware(hardware)
def test_adrv9002_stream_profile_write_both(iio_uri):
    import adi

    sdr = adi.adrv9002(iio_uri)
    sdr.write_stream_profile(lte_14_stream, lte_14_profile)


#########################################
# It depends on test_adrv9002_nco_write_profile to be run first.
# Maybe we should think in adding something like pytest-dependency
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_adrv9002_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_adrv9002_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.skip(reason="Test still fails on chan1")
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
def test_adrv9002_cw_loopback(test_cw_loopback, iio_uri, classname, channel, param_set):
    test_cw_loopback(iio_uri, classname, channel, param_set)
