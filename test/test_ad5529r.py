import pytest

hardware = "ad5529r"
classname = "adi.ad552xr"
channels = [f"voltage{i}" for i in range(16)]


#########################################
# Raw attribute test
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("sub_channel", channels)
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats", [("raw", 0, 65535, 5000, 1, 3)],
)
def test_ad552xr_raw(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
# Channel output configuration test
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", channels)
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "range_sel",
            [
                "unipolar_5V",
                "unipolar_10V",
                "unipolar_20V",
                "unipolar_40V",
                "bipolar_5V",
                "bipolar_10V",
                "bipolar_15V",
                "bipolar_20V",
            ],
        ),
        ("output_state", ["disable", "enable"]),
    ],
)
def test_ad552xr_output_cfg(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)


#########################################
# DAC Configuration tests
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("sub_channel", channels)
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("input_register_a", 0, 65535, 5000, 1, 3),
        ("input_register_b", 0, 65535, 5000, 1, 3),
    ],
)
def test_ad552xr_input_registers_a_b(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", channels)
@pytest.mark.parametrize(
    "attr, val", [("hw_sw_sel", ["hw", "sw"]),],
)
def test_ad552xr_hw_sw_sel(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", channels)
@pytest.mark.parametrize(
    "attr, val",
    [("func_sel", ["disable", "ldac_toggle", "dither", "sawtooth", "triangular"],),],
)
def test_ad552xr_func_sel(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", channels)
@pytest.mark.parametrize(
    "attr, val",
    [
        (
            "hw_ldac_pin_sel",
            ["ldac_toggle_0", "ldac_toggle_1", "ldac_toggle_2", "ldac_toggle_3",],
        ),
        ("hw_ldac_edge_sel", ["rising_edge", "falling_edge", "any_edge"]),
    ],
)
def test_ad552xr_func_ldac_toggle_cfg(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("subchannel", channels)
@pytest.mark.parametrize(
    "attr, val",
    [
        ("dither_period_factor", ["2", "4", "8", "16", "32", "64", "128"]),
        ("dither_phase", ["0", "90", "180", "270"]),
    ],
)
def test_ad552xr_func_dither_cfg(
    test_attribute_multiple_values, iio_uri, classname, subchannel, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0, 1, 0, subchannel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("sub_channel", channels)
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats", [("ramp_step_size", 0, 255, 5, 0, 3)],
)
def test_ad552xr_func_sawtooth_triangular_cfg(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )


#########################################
# Channel readonly attributes
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("sub_channel", channels)
@pytest.mark.parametrize("attr", ["offset", "scale"])
def test_ad552xr_channel_readonly_attr(
    test_attribute_single_value_channel_readonly, iio_uri, classname, sub_channel, attr,
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, sub_channel, attr)


#########################################
# Device-level attributes
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val", [("sampling_frequency", ["500000"]),],
)
def test_ad552xr_device_attr(
    test_attribute_multiple_values, iio_uri, classname, attr, val
):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)
