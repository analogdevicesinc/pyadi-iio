import iio

import adi
import numpy as np
import pytest

hardware = [
    "adrv9361"
]
classname = "adi.ad9361"

##################################

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("tx_hardwaregain_chan0", -20.0, -7.0, 1, 0, 10),
        ("tx_hardwaregain_chan1", -20.0, -7.0, 1, 0, 10)
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
                rx_rf_port_select="A_BALANCED",
                tx_rf_port_select="A",
                tx_lo=2300000000,
                rx_lo=2400000000,
                tx_hardwaregain_chan0=-10,
                tx_hardwaregain_chan1=-10,
                gain_control_mode_chan0="slow_attack",
                gain_control_mode_chan1="slow_attack",
                rx_rf_bandwidth=18000000,
                tx_rf_bandwidth=18000000,
            ),
        ),
        (
            0.0,
            75,
            150,
            dict(
                sample_rate=30720000,
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                tx_lo=2300000000,
                rx_lo=2400000000,
            ),
        ),
        (
            0.4,
            10,
            50,
            dict(
                rx_rf_port_select="A_BALANCED",
                tx_rf_port_select="A",
                rx_lo=2400000000,
                tx_lo=2400000000,
                sample_rate=30720000,
            ),
        ),
        (
            0.4,
            10,
            50,
            dict(
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                rx_lo=2400000000,
                tx_lo=2400000000,
                sample_rate=30720000,
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
    "dds_scale, frequency, hardwaregain_low, hardwaregain_high, param_set",
    [
        (
            0.0,
            999859,
            50,
            80,
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="A_BALANCED",
                tx_rf_port_select="A",
                sample_rate=30720000,
            ),
        ),
        (
            0.0,
            999859,
            50,
            80,
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                sample_rate=30720000,
            ),
        ),
        (
            0.4,
            999859,
            0.0,
            28,
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="A_BALANCED",
                tx_rf_port_select="A",
                sample_rate=30720000,
            ),
        ),
        (
            0.4,
            999859,
            0.0,
            28,
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                sample_rate=30720000,
            ),
        ),
    ],
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
    param_set,
):
    test_hardwaregain(
        iio_uri,
        classname,
        channel,
        dds_scale,
        frequency,
        hardwaregain_low,
        hardwaregain_high,
        param_set,
    )


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
def test_ad9361_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_dcxo(test_dcxo_calibration, context_desc, classname, iio_uri):
    test_dcxo_calibration(context_desc, classname, iio_uri)

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
            rx_rf_port_select="A_BALANCED",
            tx_rf_port_select="A",
        ),
        dict(
            sample_rate=30720000,
            tx_lo=2400000000,
            rx_lo=2400000000,
            rx_rf_port_select="B_BALANCED",
            tx_rf_port_select="B",
        ),
    ],
)
def test_ad9361_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set,frequency, scale",
    [
        (
            dict(
            tx_lo=2400000000,
            rx_lo=2400000000,
            rx_rf_port_select="A_BALANCED",
            tx_rf_port_select="A",
            sample_rate=30720000,
            ),
            2999577, 0.0625,
        ),
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                sample_rate=30720000,
            ),
            2999577, 0.0625,
        )
    ],
)
@pytest.mark.parametrize(
    "low, high",
    [([-20.0, -100.0, -120.0, -120.0, -120.0], [-10.0, -60.0, -75.0, -75.0, -80.0])],
)
def test_harmonic_values(
    test_harmonics, classname, iio_uri, channel, param_set, low, high, frequency, scale, plot=False
):
    test_harmonics(classname, iio_uri, channel, param_set, low, high, frequency, scale, plot)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale",
    [
        (
            dict(
            tx_lo=2400000000,
            rx_lo=2400000000,
            rx_rf_port_select="A_BALANCED",
            tx_rf_port_select="A",
            sample_rate=30720000,
            ),
            2999577, 0.0625,
        ),
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                rx_rf_port_select="B_BALANCED",
                tx_rf_port_select="B",
                sample_rate=30720000,
            ),
            2999577, 0.0625,
        )
    ],
)
@pytest.mark.parametrize(
    "low, high",
    [([-20.0, -120.0, -120.0, -125.0], [-10.0, -75.0, -75.0, -80.0])],
)
def test_peaks(test_sfdrl, classname, iio_uri, channel, param_set, low, high, frequency, scale, plot=False):
    test_sfdrl(classname, iio_uri, channel, param_set, low, high, frequency, scale, plot)
