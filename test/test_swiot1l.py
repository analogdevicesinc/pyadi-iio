import numpy as np
import pytest

import adi

hardware = "swiot1l"

# Default channel config used by all runtime tests.
# CH0-CH1: ad74413r voltage inputs (ADC), CH2: ad74413r voltage output, CH3: max14906 digital output.
CHANNEL_CONFIG = [
    ("ad74413r", "voltage_in"),
    ("ad74413r", "voltage_in"),
    ("ad74413r", "voltage_out"),
    ("max14906", "output"),
]


def configure_and_connect(uri):
    """Switch the board to config mode, apply CHANNEL_CONFIG, switch to runtime,
    and return a fresh swiot1l instance connected in runtime mode."""
    board = adi.swiot1l(uri=uri)

    # Enter config mode if not already there
    if board.mode != "config":
        board.mode = "config"
        board = adi.swiot1l(uri=uri)

    for i, (device, function) in enumerate(CHANNEL_CONFIG):
        setattr(board, f"ch{i}_device", device)
        setattr(board, f"ch{i}_function", function)
        setattr(board, f"ch{i}_enable", 1)

    board.mode = "runtime"

    return adi.swiot1l(uri=uri)


# -- swiot config modes -------------------------------------------------------


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_starts_in_config_mode(iio_uri):
    """Board should power up / reset into config mode."""
    board = adi.swiot1l(uri=iio_uri)
    assert board.mode == "config"


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_config_channel_attributes(iio_uri):
    """Write and read back ch0 device/function while in config mode."""
    board = adi.swiot1l(uri=iio_uri)
    if board.mode != "config":
        board.mode = "config"
        board = adi.swiot1l(uri=iio_uri)

    board.ch0_device = "ad74413r"
    board.ch0_function = "voltage_in"
    board.ch0_enable = 1

    assert board.ch0_device == "ad74413r"
    assert board.ch0_function == "voltage_in"
    assert int(board.ch0_enable) == 1


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_config_to_runtime_transition(iio_uri):
    """Board must accept a config -> runtime mode switch."""
    board = configure_and_connect(iio_uri)
    assert board.mode == "runtime"


# -- ADT75 temperature sensor --------------------------------------------------


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_adt75_temperature(iio_uri):
    board = configure_and_connect(iio_uri)
    temp = board.adt75()
    assert 0 < temp < 80


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_adt75_max_threshold(iio_uri):
    """Write and read back the ADT75 over-temperature threshold."""
    board = configure_and_connect(iio_uri)
    board.adt75.max = 60000  # millidegrees
    assert board.adt75.max == 60000


# -- MAX14906 digital I/O ------------------------------------------------------


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_max14906_output_raw(iio_uri):
    """Toggle a MAX14906 output channel and verify the readback."""
    board = configure_and_connect(iio_uri)
    ch = board.max14906.channel["voltage3"]

    ch.raw = 1
    assert int(ch.raw) == 1

    ch.raw = 0
    assert int(ch.raw) == 0


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_max14906_do_mode(iio_uri):
    """Write and read back the do_mode attribute of an output channel."""
    board = configure_and_connect(iio_uri)
    ch = board.max14906.channel["voltage3"]

    original = ch.do_mode
    # Toggle through available modes and restore
    available = ch.do_mode_available.split()
    for mode in available:
        ch.do_mode = mode
        assert ch.do_mode == mode

    ch.do_mode = original


# -- AD74413R analog I/O -------------------------------------------------------


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_ad74413r_channel_scale(iio_uri):
    """Scale attribute on an ADC input channel should be non-zero."""
    board = configure_and_connect(iio_uri)
    scale = board.ad74413r.rx_channel["voltage0"].scale
    assert float(scale) != 0


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_ad74413r_sampling_frequency(iio_uri):
    """Write and read back the sampling frequency on an ADC channel."""
    board = configure_and_connect(iio_uri)
    ch = board.ad74413r.rx_channel["voltage0"]

    ch.sampling_frequency = 4800
    assert int(ch.sampling_frequency) == 4800


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_ad74413r_dac_raw(iio_uri):
    """Write a raw value to an AD74413R DAC output channel."""
    board = configure_and_connect(iio_uri)
    ch = board.ad74413r.tx_channel["voltage2"]

    ch.raw = 0
    assert int(ch.raw) == 0


# -- AD74413R IIO buffer capture -----------------------------------------------


@pytest.mark.iio_hardware(hardware)
def test_swiot1l_ad74413r_iio_buffer(iio_uri):
    board = configure_and_connect(iio_uri)

    adc = board.ad74413r
    adc.rx_output_type = "SI"
    adc.rx_enabled_channels = ["voltage0"]
    adc.rx_buffer_size = 1024
    adc.sample_rate = 4800

    data = adc.rx()
    adc.rx_destroy_buffer()

    samples = data if not isinstance(data, list) else data[0]
    assert len(samples) == 1024
    assert np.max(np.abs(samples)) > 0
