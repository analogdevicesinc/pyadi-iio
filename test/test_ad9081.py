from os import listdir
from os.path import dirname, join, realpath

import pytest

hardware = "ad9081"
classname = "adi.ad9081"

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr, tol", [("loopback_mode", 0)])
@pytest.mark.parametrize("val", [0, 1, 2])
def test_ad9081_loopback_attr(
    test_attribute_single_value_str, iio_uri, classname, attr, val, tol
):
    test_attribute_single_value_str(iio_uri, classname, attr, val, tol)

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



#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad9081_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad9081_tx_data(test_dma_tx, iio_uri, classname, channel):
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
def test_ad9081_cyclic_buffers(
    test_cyclic_buffer, iio_uri, classname, channel, param_set
):
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
        )
    ],
)
def test_ad9081_cyclic_buffers_exception(
    test_cyclic_buffer_exception, iio_uri, classname, channel, param_set
):
    test_cyclic_buffer_exception(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad9081_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
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
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_ad9081_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware)
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
@pytest.mark.parametrize("peak_min", [-40])
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
    test_dds_loopback(
        iio_uri, classname, param_set, channel, frequency, scale, peak_min
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            loopback_mode=0,
            rx_main_nco_frequencies=[500000000, 500000000, 500000000, 500000000],
            tx_main_nco_frequencies=[500000000, 500000000, 500000000, 500000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0],
        ),
        dict(
            loopback_mode=0,
            rx_main_nco_frequencies=[750000000, 750000000, 750000000, 750000000],
            tx_main_nco_frequencies=[750000000, 750000000, 750000000, 750000000],
            rx_channel_nco_frequencies=[0, 0, 0, 0],
            tx_channel_nco_frequencies=[0, 0, 0, 0],
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
    test_iq_loopback(iio_uri, classname, channel, param_set)
