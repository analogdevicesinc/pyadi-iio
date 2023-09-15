import pytest

hardware = ["pluto", "pluto_rev_c"]
classname = "adi.Pluto"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("tx_hardwaregain_chan0", -89.75, 0.0, 0.25, 0, 100),
        ("rx_lo", 325000000, 3800000000, 1, 8, 100),
        ("tx_lo", 325000000, 3800000000, 1, 8, 100),
        ("sample_rate", 2084000, 61440000, 1, 4, 100),
        ("loopback", 0, 0, 1, 0, 0),
        ("loopback", 1, 1, 1, 0, 0),
        ("loopback", 2, 2, 1, 0, 0),
    ],
)
def test_pluto_attr(
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
@pytest.mark.parametrize("channel", [0])
def test_pluto_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_pluto_tx_data(test_dma_tx, iio_uri, classname, channel):
    test_dma_tx(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
def test_pluto_cyclic_buffers(
    test_cyclic_buffer, iio_uri, classname, channel, param_set
):
    test_cyclic_buffer(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
def test_pluto_cyclic_buffers_exception(
    test_cyclic_buffer_exception, iio_uri, classname, channel, param_set
):
    test_cyclic_buffer_exception(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_pluto_loopback(test_dma_loopback, iio_uri, classname, channel):
    test_dma_loopback(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        )
    ],
)
@pytest.mark.parametrize("sfdr_min", [40])
def test_pluto_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min):
    test_sfdr(iio_uri, classname, channel, param_set, sfdr_min)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("frequency, scale", [(1000000, 1)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-30,
            sample_rate=4000000,
        )
    ],
)
@pytest.mark.parametrize("peak_min", [-40])
def test_pluto_dds_loopback(
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
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_lo=1000000000,
            rx_lo=1000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=2000000000,
            rx_lo=2000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
        dict(
            tx_lo=3000000000,
            rx_lo=3000000000,
            gain_control_mode_chan0="slow_attack",
            tx_hardwaregain_chan0=-20,
            sample_rate=4000000,
        ),
    ],
)
def test_pluto_iq_loopback(test_iq_loopback, iio_uri, classname, channel, param_set):
    test_iq_loopback(iio_uri, classname, channel, param_set)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_pluto_loopback_zeros(test_dma_dac_zeros, iio_uri, classname, channel):
    test_dma_dac_zeros(iio_uri, classname, channel)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("buffer_size", [2 ** 20])
@pytest.mark.parametrize("sample_rate", [600e3])
def test_pluto_verify_overflow(
    test_verify_overflow, iio_uri, classname, channel, buffer_size, sample_rate
):
    test_verify_overflow(iio_uri, classname, channel, buffer_size, sample_rate)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("buffer_size", [2 ** 20])
@pytest.mark.parametrize("sample_rate", [600e3])
def test_pluto_verify_underflow(
    test_verify_underflow, iio_uri, classname, channel, buffer_size, sample_rate
):
    test_verify_underflow(iio_uri, classname, channel, buffer_size, sample_rate)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("loopback", [0, 1])
@pytest.mark.parametrize("toggle_sr", [0, 1])
def test_repeat_sample_rate_updates(iio_uri, loopback, toggle_sr):
    # This test should be run with Pluto with cabled loopback
    import adi
    import time
    import numpy as np

    sdr = adi.Pluto(uri=iio_uri)
    sdr.loopback = loopback
    sdr.rx_rf_bandwidth = 4000000
    sdr.rx_lo = 2000000000
    sdr.tx_lo = 2000000000
    sdr.tx_cyclic_buffer = True
    sdr.tx_hardwaregain_chan0 = -53
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = 50
    sdr.sample_rate = 7.5e6

    sdr.rx_enabled_channels = [0]
    sdr.tx_enabled_channels = [0]

    # Create a sinewave waveform
    fs = int(sdr.sample_rate)
    N = 1024
    fc = int(1000000 / (fs / N)) * (fs / N)
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q

    # Send data
    sdr.tx(iq)

    peaks = []

    # Collect data
    for r in range(20):
        if toggle_sr:
            sdr.sample_rate = 7.5e6  # THIS SEEMS TO TOGGLE THE BEHAVIOR
        sdr.tx_destroy_buffer()
        sdr.tx(iq)

        # Wait for transmitter to become ready
        time.sleep(1)

        # Flush old data from buffers
        for _ in range(100):
            x = sdr.rx()

        peak = np.max(np.abs(x))
        print(f"Run {r} | Peak: {peak}")

        peaks.append(peak)

    del sdr

    # Compare delta in peaks
    assert np.max(peaks) - np.min(peaks) < 400
