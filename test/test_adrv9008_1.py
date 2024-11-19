from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = "adrv9008-1"
classname = "adi.adrv9008_1"

profile_path = dirname(realpath(__file__)) + "/adrv9009_profiles/"
test_profiles = [join(profile_path, f) for f in listdir(profile_path)]

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value",
    [
        ("ensm_mode", "radio_off"),
        ("ensm_mode", "radio_on"),
        ("calibrate_rx_phase_correction_en", 1),
        ("calibrate_rx_phase_correction_en", 0),
        ("calibrate_rx_qec_en", 1),
        ("calibrate_rx_qec_en", 0),
        ("rx_quadrature_tracking_en_chan0", 1),
        ("rx_quadrature_tracking_en_chan0", 0),
        ("rx_quadrature_tracking_en_chan1", 1),
        ("rx_quadrature_tracking_en_chan1", 0),
        ("rx_powerdown_en_chan0", 1),
        ("rx_powerdown_en_chan0", 0),
        ("rx_powerdown_en_chan1", 1),
        ("rx_powerdown_en_chan1", 0),
        ("gain_control_mode_chan0", "manual"),
        ("gain_control_mode_chan0", "slow_attack"),
        ("gain_control_mode_chan1", "manual"),
        ("gain_control_mode_chan1", "slow_attack"),
    ],
)
def test_adrv9008_1_attr_boolean(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("rx_rf_bandwidth"), ("rx_sample_rate"),],
)
def test_adrv9008_1_attr_boolean_readonly(
    test_attribute_single_value_boolean_readonly, iio_uri, classname, attr
):
    test_attribute_single_value_boolean_readonly(iio_uri, classname, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value", [("calibrate", 1),],
)
def test_adrv9008_1_attribute_write_only_str(
    test_attribute_write_only_str, iio_uri, classname, attr, value
):
    test_attribute_write_only_str(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol", [("trx_lo", 70000000, 6000000000, 1000, 0),],
)
def test_adrv9008_1_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, depends, start, stop, step, tol, repeats",
    [
        (
            "rx_hardwaregain_chan0",
            dict(
                frequency_hopping_mode_en=0,
                ensm_mode="radio_on",
                gain_control_mode_chan0="manual",
                rx_powerdown_en_chan0=0,
            ),
            0.0,
            30.0,
            0.5,
            0.05,
            2,
        ),
        (
            "rx_hardwaregain_chan1",
            dict(
                ensm_mode="radio_on",
                gain_control_mode_chan1="manual",
                rx_powerdown_en_chan1=0,
            ),
            0.0,
            30.0,
            0.5,
            0.05,
            2,
        ),
    ],
)
def test_adrv9008_1_attr_singleval_depends(
    test_attribute_check_range_singleval_with_depends,
    iio_uri,
    classname,
    attr,
    depends,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_check_range_singleval_with_depends(
        iio_uri, classname, attr, depends, start, stop, step, tol, repeats
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["profile"])
@pytest.mark.parametrize(
    "files", test_profiles,
)
def test_adrv9008_1_profile_write(
    test_attribute_write_only_str, iio_uri, classname, attr, files
):
    test_attribute_write_only_str(iio_uri, classname, attr, files)
