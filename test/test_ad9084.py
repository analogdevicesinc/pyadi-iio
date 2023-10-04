from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = ["ad9084", "ad9084_tdd"]
classname = "adi.ad9084"


def scale_field(param_set, iio_uri):
    # Scale fields to match number of channels
    import adi

    dev = adi.ad9084(uri=iio_uri)
    for field in param_set:
        if param_set[field] is not list:
            continue
        existing_val = getattr(dev, field)
        param_set[field] = param_set[field][0] * len(existing_val)
    return param_set


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("rx_nyquist_zone", ["even", "odd"]),
        (
            "rx_test_mode",
            [
                "midscale_short",
                "pos_fullscale",
                "neg_fullscale",
                "checkerboard",
                "pn23",
                "pn9",
                "one_zero_toggle",
                "user",
                "pn7",
                "pn15",
                "pn31",
                "ramp",
                "off",
            ],
        ),
    ],
)
def test_ad9084_str_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("rx_main_nco_frequencies", -2000000000, 2000000000, 1, 3, 10),
        ("tx_main_nco_frequencies", -6000000000, 6000000000, 1, 3, 10),
        ("rx_channel_nco_frequencies", -500000000, 500000000, 1, 3, 10),
        ("tx_channel_nco_frequencies", -750000000, 750000000, 1, 3, 10),
        ("rx_main_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_main_nco_phases", -180000, 180000, 1, 1, 10),
        ("rx_channel_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_channel_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_main_nco_test_tone_scales", 0.0, 1.0, 0.01, 0.01, 10),
        ("tx_channel_nco_test_tone_scales", 0.0, 1.0, 0.01, 0.01, 10),
    ],
)
def test_ad9084_attr(
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
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad9084_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad9084_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_nyquist_zone=["odd", "odd", "odd", "odd"],
            tx_channel_nco_gain_scales=[0.5, 0.5, 0.5, 0.5],
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_test_tone_en=[0, 0, 0, 0],
            tx_main_nco_test_tone_en=[0, 0, 0, 0],
        )
    ],
)
def test_ad9084_cyclic_buffers(
    test_cyclic_buffer, iio_uri, classname, channel, param_set
):
    param_set = scale_field(param_set, iio_uri)
    test_cyclic_buffer(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_test_tone_en=[0, 0, 0, 0],
            tx_main_nco_test_tone_en=[0, 0, 0, 0],
        )
    ],
)
def test_ad9084_cyclic_buffers_exception(
    test_cyclic_buffer_exception, iio_uri, classname, channel, param_set
):
    param_set = scale_field(param_set, iio_uri)
    test_cyclic_buffer_exception(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_test_tone_en=[0, 0, 0, 0],
            tx_main_nco_test_tone_en=[0, 0, 0, 0],
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [70])
def test_ad9084_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    param_set = scale_field(param_set, iio_uri)
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min, full_scale=0.5)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("frequency, scale", [(10000000, 0.5)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
        )
    ],
)
@pytest.mark.parametrize("peak_min", [-30])
def test_ad9084_dds_loopback(
    test_dds_loopback,
    iio_uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
):
    param_set = scale_field(param_set, iio_uri)
    test_dds_loopback(
        iio_uri, classname, param_set, channel, frequency, scale, peak_min
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_main_nco_frequencies=[500000000, 500000000, 500000000, 500000000],
            tx_main_nco_frequencies=[500000000, 500000000, 500000000, 500000000],
            rx_channel_nco_frequencies=[1234567, 1234567, 1234567, 1234567],
            tx_channel_nco_frequencies=[1234567, 1234567, 1234567, 1234567],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
        ),
        dict(
            rx_main_nco_frequencies=[750000000, 750000000, 750000000, 750000000],
            tx_main_nco_frequencies=[750000000, 750000000, 750000000, 750000000],
            rx_channel_nco_frequencies=[-1234567, -1234567, -1234567, -1234567],
            tx_channel_nco_frequencies=[-1234567, -1234567, -1234567, -1234567],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
        ),
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
        ),
    ],
)
def test_ad9084_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    param_set = scale_field(param_set, iio_uri)
    test_iq_loopback(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("frequency", [10000000])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1010000000, 1010000000, 1010000000, 1010000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_main_nco_test_tone_scales=[0.5, 0.5, 0.5, 0.5],
            tx_main_nco_test_tone_en=[1, 1, 1, 1],
            tx_channel_nco_test_tone_en=[0, 0, 0, 0],
        ),
        dict(
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[10000000, 10000000, 10000000, 10000000],
            tx_channel_nco_test_tone_scales=[0.5, 0.5, 0.5, 0.5],
            tx_main_nco_test_tone_en=[0, 0, 0, 0],
            tx_channel_nco_test_tone_en=[1, 1, 1, 1],
        ),
    ],
)
@pytest.mark.parametrize("peak_min", [-30])
def test_ad9084_nco_loopback(
    test_tone_loopback, iio_uri, classname, param_set, channel, frequency, peak_min,
):
    param_set = scale_field(param_set, iio_uri)
    test_tone_loopback(iio_uri, classname, param_set, channel, frequency, peak_min)


#########################################
