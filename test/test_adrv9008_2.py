from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = "adrv9009"
classname = "adi.adrv9008_2"

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
        ("calibrate_tx_qec_en", 1),
        ("calibrate_tx_qec_en", 0),
        ("tx_quadrature_tracking_en_chan0", 1),
        ("tx_quadrature_tracking_en_chan0", 0),
        ("tx_quadrature_tracking_en_chan1", 1),
        ("tx_quadrature_tracking_en_chan1", 0),
        ("obs_quadrature_tracking_en", 1),
        ("obs_quadrature_tracking_en", 0),
        ("obs_rf_port_select", "OBS_AUX_LO"),
        ("obs_rf_port_select", "OBS_TX_LO"),
        ("obs_powerdown_en", 1),
        ("obs_powerdown_en", 0),
    ],
)
def test_adrv9008_2_attr_boolean(
    test_attribute_single_value_boolean, iio_uri, classname, attr, value
):
    test_attribute_single_value_boolean(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", [("tx_rf_bandwidth"), ("tx_sample_rate"), ("orx_sample_rate"),],
)
def test_adrv9008_2_attr_boolean_readonly(
    test_attribute_single_value_boolean_readonly, iio_uri, classname, attr
):
    test_attribute_single_value_boolean_readonly(iio_uri, classname, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, value", [("calibrate", 1),],
)
def test_adrv9008_2_attribute_write_only_str(
    test_attribute_write_only_str, iio_uri, classname, attr, value
):
    test_attribute_write_only_str(iio_uri, classname, attr, value)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("trx_lo", 70000000, 6000000000, 1000, 0),
        ("aux_obs_lo", 70000000, 6000000000, 1000, 0),
    ],
)
def test_adrv9008_2_attr(
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
            "tx_hardwaregain_chan0",
            dict(frequency_hopping_mode_en=0, ensm_mode="radio_on",),
            -41.95,
            0.0,
            0.05,
            0.05,
            2,
        ),
        (
            "tx_hardwaregain_chan1",
            dict(frequency_hopping_mode_en=0, ensm_mode="radio_on",),
            -41.95,
            0.0,
            0.05,
            0.05,
            2,
        ),
    ],
)
def test_adrv9008_2_attr_singleval_depends(
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
@pytest.mark.parametrize(
    "attr, depends, start, stop, step, tol, repeats",
    [
        (
            "obs_hardwaregain",
            dict(
                frequency_hopping_mode_en=0, ensm_mode="radio_on", obs_powerdown_en=0,
            ),
            0.0,
            30.0,
            0.5,
            0.05,
            2,
        ),
    ],
)
def test_adrv9008_2_attr_singleval_depends_2(
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
def test_adrv9008_2_profile_write(
    test_attribute_write_only_str, iio_uri, classname, attr, files
):
    test_attribute_write_only_str(iio_uri, classname, attr, files)
