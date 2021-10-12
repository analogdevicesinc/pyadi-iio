import iio

import adi
import numpy as np
import pytest

hardware = ["packrf", "adrv9361", "fmcomms3", "ad9361"]
classname = "adi.ad9361"

##################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "voltage_raw, low, high",
    [
        ("in_temp0", 80, 160),
        ("in_voltage0", 3045, 3629),
        ("in_voltage1", 3045, 3629),
        ("in_voltage2", 3045, 3629),
        ("in_voltage3", 1231, 1393),
        ("in_voltage4", 1661, 2749),
        ("in_voltage5", 1231, 1393),
    ],
)
def test_ad7291(context_desc, voltage_raw, low, high):
    ctx = None
    for ctx_desc in context_desc:
        if ctx_desc["hw"] in hardware:
            ctx = iio.Context(ctx_desc["uri"])
    if not ctx:
        pytest.skip("No valid hardware found")

    ad7291 = ctx.find_device("ad7291")

    for channel in ad7291.channels:
        c_name = "out" if channel.output else "in"
        c_name += "_" + str(channel.id)
        if c_name == voltage_raw:
            for attr in channel.attrs:
                if attr == "raw":
                    try:
                        print(channel.attrs[attr].value)
                        assert low <= int(channel.attrs[attr].value) <= high
                    except OSError:
                        continue


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("tx_hardwaregain_chan0", -30.0, -7.0, 0.25, 0, 100),
        ("tx_hardwaregain_chan1", -30.0, -7.0, 0.25, 0, 100),
        ("rx_lo", 2300000000, 2500000000, 1, 8, 100),
        ("tx_lo", 2300000000, 2500000000, 1, 8, 100),
        ("sample_rate", 30700000, 30740000, 1, 4, 20),
        ("rx_rf_bandwidth", 16000000, 19000000, 1, 4, 10),
        ("tx_rf_bandwidth", 16000000, 19000000, 1, 4, 10),
    ],
)
def test_ad9361_attr(
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


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "dds_scale, min_rssi, max_rssi, param_set",
    [
        (
            0.0,
            75,
            150,
            dict(
                sample_rate=30720000,
                tx_lo=2300000000,
                rx_lo=2400000000,
                gain_control_mode_chan0="slow_attack",
                gain_control_mode_chan1="slow_attack",
                rx_rf_bandwidth=18000000,
                tx_rf_bandwidth=18000000,
            ),
        ),
        (
            0.4,
            10,
            50,
            dict(
                gain_control_mode_chan0="slow_attack",
                gain_control_mode_chan1="slow_attack",
                rx_lo=2400000000,
                tx_lo=2400000000,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                sample_rate=30720000,
                rx_rf_bandwidth=18000000,
                tx_rf_bandwidth=18000000,
            ),
        ),
    ],
)
def test_rssi(
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


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "dds_scale, frequency, hardwaregain_low, hardwaregain_high",
    [(0.0, 999859, 50, 80), (0.4, 999859, 0.0, 28)],
)
def test_hardware_gain(
    test_hardwaregain,
    iio_uri,
    classname,
    channel,
    dds_scale,
    frequency,
    hardwaregain_low,
    hardwaregain_high,
):
    test_hardwaregain(
        iio_uri,
        classname,
        channel,
        dds_scale,
        frequency,
        hardwaregain_low,
        hardwaregain_high,
    )


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_ad9361_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            sample_rate=30720000,
            tx_lo=2400000000,
            rx_lo=2400000000,
            gain_control_mode_chan0="slow_attack",
            gain_control_mode_chan1="slow_attack",
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            rx_rf_bandwidth=18000000,
            tx_rf_bandwidth=18000000,
        ),
    ],
)
def test_ad9361_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_dcxo(test_dcxo_calibration, classname, iio_uri):
    test_dcxo_calibration(classname, iio_uri)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=2400000000,
            rx_lo=2400000000,
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            sample_rate=30720000,
        )
    ],
)
@pytest.mark.parametrize(
    "low, high",
    [([-20.0, -100.0, -110.0, -110.0, -110.0], [-10.0, -60.0, -75.0, -75.0, -80.0])],
)
def test_harmonic_values(
    test_harmonics, classname, iio_uri, channel, param_set, low, high, plot=False
):
    test_harmonics(classname, iio_uri, channel, param_set, low, high, plot)
