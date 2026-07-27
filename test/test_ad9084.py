from os import listdir
from os.path import dirname, join, realpath

import pytest

# hardware = ["ad9084", "ad9084_tdd"] # older builds
hardware = ["adsy1100"]
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
@pytest.mark.parametrize("channel", [0, 1])
def test_ad9084_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
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
@pytest.mark.parametrize("channel", [0, 1])
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
@pytest.mark.iio_hardware("adsy1100")
def test_split_rx_buffers(iio_uri):
    import adi

    dev = adi.ad9084(uri=iio_uri)
    dev.rx_buffer_size = 2 ** 10

    d = dev.rx()
    d1 = dev.rx1()
    d2 = dev.rx2()

    assert d is not None
    assert d1 is not None
    assert d2 is not None


#########################################
@pytest.mark.iio_hardware("adsy1100")
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("use_tx2", [False, True])
def test_ad9084_tx_data_split_buffers(
    test_dma_tx, iio_uri, classname, channel, use_tx2
):
    test_dma_tx(iio_uri, classname, channel, use_tx2)


#########################################
PFILT_CONFIG = """# pfilt_coeffs_16_lp0.txt
mode: real_n2 real_n2
gain: 6 6 6 6
scalar_gain: 63 63 63 63
dest: rx pfilt_all bank_0
hc_delay: 0
mode_switch_en: 0
mode_switch_add_en: 0
real_data_mode_en: 1
quad_mode_en: 0
0x00F2
0xFDE3
0x0096
0x04B8
"""

CFIR_CONFIG = """# cfir_coeffs_16_lp0.txt
dest: rx cfir_all profile_2 datapath_all
gain: 0
complex_scalar: 32767 0
enable: 1 profile_2
selection_mode: direct_regmap
coeff_transfer: 0
bypass: 0
242 242
541 541
151 151
64329 64329
"""


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "attr, config",
    [("pfilt_config", PFILT_CONFIG), ("cfir_config", CFIR_CONFIG)],
    ids=["pfilt", "cfir"],
)
def test_ad9084_filter_config(iio_uri, tmp_path, attr, config):
    import adi

    dev = adi.ad9084(uri=iio_uri)
    config_file = tmp_path / "{}.txt".format(attr)
    config_file.write_text(config)
    setattr(dev, attr, str(config_file))
