# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""Emulated (pytest-libiio) tests for the out-of-tree MAXM86161 driver.

These tests do NOT require MAXM86161 hardware. They run against an emulated
IIO context served by ``iio-emu`` from ``test/emu/devices/maxm86161.xml``.

Run them with::

    pytest test/ --emu \
        --custom-hw-map=test/emu/hardware_map.yml \
        --emu-xml-dir=test/emu/devices

Requirements: ``iio-emu`` on PATH, plus ``pytest-libiio``, ``pylibiio`` and
``pyadi-iio`` installed. The ``iio_hardware("maxm86161", ...)`` marker skips
each test automatically when hardware/emulation is not available.

See https://pytest-libiio.readthedocs.io/en/latest/emulation/
"""

import pytest

import adi

HARDWARE = "maxm86161"


def _open(uri):
    """Open the MAXM86161 driver against the (emulated) context URI."""
    return adi.maxm86161(uri=uri)


@pytest.mark.iio_hardware(HARDWARE, False)
def test_device_creation(iio_uri):
    """The driver can attach to the emulated maxm86161 device."""
    dev = _open(iio_uri)
    assert dev._ctrl is not None
    assert dev._rxadc is not None
    assert dev._ctrl.name == "maxm86161"


@pytest.mark.iio_hardware(HARDWARE, False)
def test_wrong_device_name_raises(iio_uri):
    """Requesting an incompatible device name raises."""
    with pytest.raises(Exception):
        adi.maxm86161(uri=iio_uri, device_name="not_a_maxm86161")


@pytest.mark.iio_hardware(HARDWARE, False)
def test_rx_channel_names(iio_uri):
    """The declared rx channel is present on the emulated device."""
    dev = _open(iio_uri)
    assert dev._rx_channel_names == ["voltage0"]


# Attribute status read
@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize(
    "attr",
    [
        "part_id",
        "rev_id",
        "interrupt_status",
        "die_temperature",
        "fifo_count",
        "fifo_overflow_count",
    ],
)
def test_readonly_attrs_readable(iio_uri, attr):
    """Read-only debug attributes return a value without error."""
    dev = _open(iio_uri)
    value = getattr(dev, attr)
    assert value is not None


@pytest.mark.iio_hardware(HARDWARE, False)
def test_part_id_matches_emulated_value(iio_uri):
    """part_id reflects the value baked into the emu XML (0x36)."""
    dev = _open(iio_uri)
    assert str(dev.part_id).lower().endswith("36")


# Global read/write debug attributes
GLOBAL_RW_ATTRS = [
    ("sample_rate", 2),
    ("integration_time", 3),
    ("adc_range", 2),
    ("sample_averaging", 3),
    ("alc_disable", 1),
    ("add_offset", 1),
    ("led_settling", 2),
    ("dig_filter", 1),
    ("pd_bias", 5),
    ("fifo_watermark", 15),
    ("fifo_watermark", 32),
    ("fifo_rollover", 1),
    ("fifo_rollover", 0),
    ("fifo_a_full_type", 1),
    ("led_pilot_pa", 64),
    ("prox_threshold", 128),
    ("picket_fence_enable", 1),
    ("picket_fence_order", 1),
    ("picket_fence_iir_tc", 3),
    ("picket_fence_iir_init", 2),
    ("picket_fence_threshold_sigma", 4),
    ("shutdown", 1),
    ("low_power_mode", 1),
    ("burst_enable", 1),
    ("burst_rate", 3),
    ("buffer_enable", 0),
]


@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize("attr, value", GLOBAL_RW_ATTRS)
def test_global_attr_write_read(iio_uri, attr, value):
    """Writing a global attribute is reflected on read back."""
    dev = _open(iio_uri)
    setattr(dev, attr, value)
    read_back = int(getattr(dev, attr))
    assert read_back == value


# LED sequence slots (1-6)
@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize("slot", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("value", [0, 1, 2, 3, 8, 9])
def test_led_sequence_write_read(iio_uri, slot, value):
    """Per-slot LED sequence setter is reflected by the getter."""
    dev = _open(iio_uri)
    dev.set_led_sequence(slot, value)
    assert int(dev.get_led_sequence(slot)) == value


# Per-LED drive: pulse amplitude and full-scale range (green=1, IR=2, red=3)
@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize("led", [1, 2, 3])
@pytest.mark.parametrize("value", [0, 100, 255])
def test_led_pa_write_read(iio_uri, led, value):
    """Per-LED pulse amplitude setter is reflected by the getter."""
    dev = _open(iio_uri)
    dev.set_led_pa(led, value)
    assert int(dev.get_led_pa(led)) == value


@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize("led", [1, 2, 3])
@pytest.mark.parametrize("value", [0, 1, 2, 3])
def test_led_range_write_read(iio_uri, led, value):
    """Per-LED current range setter is reflected by the getter."""
    dev = _open(iio_uri)
    dev.set_led_range(led, value)
    assert int(dev.get_led_range(led)) == value


@pytest.mark.iio_hardware(HARDWARE, False)
def test_fifo_count_readable(iio_uri):
    """fifo_count (read-only) is accessible."""
    dev = _open(iio_uri)
    assert int(dev.fifo_count) >= 0


# Buffered data capture (rx)
@pytest.mark.iio_hardware(HARDWARE, False)
@pytest.mark.parametrize("buffer_size", [16, 128])
def test_rx_capture(iio_uri, buffer_size):
    """A buffer of the requested size can be captured from the emu device."""
    dev = _open(iio_uri)
    dev.rx_buffer_size = buffer_size
    data = dev.rx()
    assert len(data) == buffer_size
    dev.rx_destroy_buffer()
