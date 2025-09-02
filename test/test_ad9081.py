import test.rf.spec as spec
from os import listdir
from os.path import dirname, join, realpath

import numpy as np
import pytest

hardware = ["ad9081", "ad9081_tdd"]
classname = "adi.ad9081"


def is_channel(channel, iio_uri):
    import adi

    dev = adi.ad9081(uri=iio_uri)
    channels = list(
        set([int("".join(filter(str.isdigit, s))) for s in dev._tx_channel_names])
    )
    return channel in channels


def scale_field(param_set, iio_uri):
    # Scale fields to match number of channels
    import adi

    dev = adi.ad9081(uri=iio_uri)
    for field in param_set:
        if isinstance(param_set[field], list):
            existing_val = getattr(dev, field)
            param_set[field] = [param_set[field][0]] * len(existing_val)
    return param_set


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("rx_nyquist_zone", ["even", "odd"]),
        ("loopback_mode", [0]),
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
        (
            "tx_main_ffh_mode",
            ["phase_continuous", "phase_incontinuous", "phase_coherent"],
        ),
    ],
)
def test_ad9081_str_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr, val", [("loopback_mode", [2, 1])])
def test_ad9081_str_attr_err(
    test_attribute_multiple_values_error, iio_uri, classname, attr, val
):
    test_attribute_multiple_values_error(iio_uri, classname, attr, val, 0)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("rx_main_nco_frequencies", -2000000000, 2000000000, 1, 1, 10),
        ("tx_main_nco_frequencies", -6000000000, 6000000000, 1, 1, 10),
        ("rx_channel_nco_frequencies", -500000000, 500000000, 1, 1, 10),
        ("tx_channel_nco_frequencies", -750000000, 750000000, 1, 1, 10),
        ("rx_main_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_main_nco_phases", -180000, 180000, 1, 1, 10),
        ("rx_channel_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_channel_nco_phases", -180000, 180000, 1, 1, 10),
        ("tx_main_nco_test_tone_scales", 0.0, 1.0, 0.01, 0.01, 10),
        ("tx_channel_nco_test_tone_scales", 0.0, 1.0, 0.01, 0.01, 10),
        ("tx_main_ffh_index", 1, 31, 1, 0, 10),
        ("tx_main_ffh_frequency", -6000000000, 6000000000, 1, 1, 10),
        ("tx_channel_nco_gain_scales", 0.0, 0.5, 0.01, 0.01, 10),
    ],
)
def test_ad9081_attr(
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
def test_ad9081_rx_data(test_dma_rx, iio_uri, classname, channel):
    if not is_channel(channel, iio_uri):
        pytest.skip("Skipping test: Channel " + str(channel) + "not available.")
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad9081_tx_data(test_dma_tx, iio_uri, classname, channel):
    if not is_channel(channel, iio_uri):
        pytest.skip("Skipping test: Channel " + str(channel) + "not available.")
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            loopback_mode=0,
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
def test_ad9081_cyclic_buffers(
    test_cyclic_buffer, iio_uri, classname, channel, param_set
):
    if not is_channel(channel, iio_uri):
        pytest.skip("Skipping test: Channel " + str(channel) + "not available.")
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
            loopback_mode=0,
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
def test_ad9081_cyclic_buffers_exception(
    test_cyclic_buffer_exception, iio_uri, classname, channel, param_set
):
    if not is_channel(channel, iio_uri):
        pytest.skip("Skipping test: Channel " + str(channel) + "not available.")
    param_set = scale_field(param_set, iio_uri)
    test_cyclic_buffer_exception(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad9081_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            loopback_mode=0,
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
def test_ad9081_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
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
            loopback_mode=0,
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
def test_ad9081_dds_loopback(
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
            loopback_mode=0,
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
            loopback_mode=0,
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
            loopback_mode=0,
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
def test_ad9081_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
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
            loopback_mode=0,
            rx_main_nco_frequencies=[1000000000, 1000000000, 1000000000, 1000000000],
            tx_main_nco_frequencies=[1010000000, 1010000000, 1010000000, 1010000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_main_nco_test_tone_scales=[0.5, 0.5, 0.5, 0.5],
            tx_main_nco_test_tone_en=[1, 1, 1, 1],
            tx_channel_nco_test_tone_en=[0, 0, 0, 0],
        ),
        dict(
            loopback_mode=0,
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
def test_ad9081_nco_loopback(
    test_tone_loopback, iio_uri, classname, param_set, channel, frequency, peak_min,
):
    param_set = scale_field(param_set, iio_uri)
    test_tone_loopback(iio_uri, classname, param_set, channel, frequency, peak_min)


#########################################
@pytest.mark.iio_hardware("ad9081_full_bw")
def test_full_bw_rx(iio_uri):
    import adi

    dev = adi.ad9081(uri=iio_uri)

    assert not dev._rx_complex_data
    assert dev._tx_complex_data

    assert dev._rx_fine_ddc_channel_names == [
        "voltage0",
        "voltage1",
        "voltage2",
        "voltage3",
    ]
    assert dev._rx_coarse_ddc_channel_names == ["voltage0", "voltage2"]
    assert dev._tx_fine_duc_channel_names == [
        "voltage0",
        "voltage1",
        "voltage2",
        "voltage3",
    ]
    assert dev._tx_coarse_duc_channel_names == ["voltage0", "voltage1"]


@pytest.mark.ad9081_loopback
@pytest.mark.iio_hardware(hardware, True)
def test_ad9081_adc_to_dac_loopback(iio_uri):
    # This example assumes an input frequency of 401 MHz
    # into ADC0. It will generate an output tone at 501 MHz
    import adi

    dev = adi.ad9081(uri=iio_uri)

    dev.loopback_mode = 1  # ADC_JESD -> DAC_JESD

    # Set all to zero but of size ref
    ref = dev.rx_channel_nco_frequencies
    dev.rx_channel_nco_frequencies = [0] * len(ref)
    ref = dev.rx_main_nco_frequencies
    dev.rx_main_nco_frequencies = [int(400e6)] * len(ref)

    ref = dev.tx_channel_nco_frequencies
    dev.tx_channel_nco_frequencies = [0] * len(ref)
    ref = dev.tx_main_nco_frequencies
    dev.tx_main_nco_frequencies = [int(500e6)] * len(ref)

    # Setup ADALM-PLUTO as generator and receiver
    pluto = adi.Pluto(uri="ip:192.168.2.1")
    pluto.dds_single_tone(int(1e6), 0.75)
    pluto.tx_lo = int(400e6)
    pluto.rx_lo = int(500e6)
    pluto.sample_rate = int(10e6)

    import time

    time.sleep(4)

    # ADC data will still stream out JESD. Check
    dev.rx_enabled_channels = [0]
    dev.rx_buffer_size = 4096
    for k in range(10):
        data = dev.rx()
    data = dev.rx()

    RXFS = dev.rx_sample_rate
    A = 2 ** 15
    fc = 1e6

    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=A, plot=False)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - fc)
    s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
    print(s)

    assert diff < RXFS * 0.01
    assert tone_peaks[indx] > -30

    # Check Pluto
    pluto.rx_enabled_channels = [0]
    pluto.rx_buffer_size = 4096
    for k in range(10):
        data = pluto.rx()
    data = pluto.rx()

    RXFS = pluto.sample_rate
    A = 2 ** 15
    fc = 1e6

    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=A, plot=False)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - fc)
    s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
    print(s)

    assert diff < RXFS * 0.01
    assert tone_peaks[indx] > -30
