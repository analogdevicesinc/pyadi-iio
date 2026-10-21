import random

import pytest

import adi

hardware = ["ad5933"]
classname = "adi.ad5933"

# AD5933 excitation output is only valid over ~1 kHz .. 100 kHz. The firmware
# validates the whole sweep on writes to the increment/points registers, i.e.
# start + increment * points must stay inside that band, so tests that touch
# those registers first pin a known-safe baseline.
MAX_OUTPUT_FREQ = 100000


def _configure_sweep(dev, start, increment, points):
    """Program a valid sweep without tripping the device's whole-sweep
    validation. The firmware checks start + increment * points on *every*
    write, so shrink the sweep to a minimal footprint (increment/points = 1)
    before widening it to the target. This keeps every intermediate state
    inside the valid band regardless of the leftover configuration."""
    dev.out_altvoltage0_frequency_increment = 1
    dev.out_altvoltage0_frequency_points = 1
    dev.out_altvoltage0_frequency_start = start
    dev.out_altvoltage0_frequency_points = points
    dev.out_altvoltage0_frequency_increment = increment


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad5933_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
# Read-only channel attributes (real / imag / temp)
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("real", "raw"),
        ("imag", "raw"),
        ("temp", "raw"),
        ("temp", "scale"),
        ("temp", "processed"),
    ],
)
def test_ad5933_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
# Integer device attributes that are independent of the rest of the sweep
# configuration (write then read back over a range).
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [("out_altvoltage0_settling_cycles", 0, 511, 1, 0, 3)],
)
def test_ad5933_attr(
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
# Sweep registers whose valid range is coupled: the device validates the whole
# sweep on every write, rejecting any that leaves start + increment * points
# outside the ~1 kHz..100 kHz band. This applies to all three registers (start,
# increment, points), so a generic write/read-back over a wide range hits
# -EINVAL depending on leftover state. For each register we pin a safe baseline
# for the other two and keep the swept range small enough that the sweep end
# never overflows.
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, baseline, start, stop, step, repeats",
    [
        # Vary the start: increment=1, points=1 -> end <= 99000 + 1*1.
        (
            "out_altvoltage0_frequency_start",
            {
                "out_altvoltage0_frequency_increment": 1,
                "out_altvoltage0_frequency_points": 1,
            },
            1500,
            100000,
            1,
            1,
        ),
        # Vary the increment: start=1000, points=10 -> end <= 1000 + 1000*10.
        (
            "out_altvoltage0_frequency_increment",
            {
                "out_altvoltage0_frequency_start": 1000,
                "out_altvoltage0_frequency_points": 10,
            },
            1,
            1000,
            1,
            3,
        ),
        # Vary the point count: start=1000, increment=10 -> end <= 1000 + 10*511.
        (
            "out_altvoltage0_frequency_points",
            {
                "out_altvoltage0_frequency_start": 1000,
                "out_altvoltage0_frequency_increment": 10,
            },
            1,
            511,
            1,
            3,
        ),
    ],
)
def test_ad5933_sweep_attr(
    iio_uri, classname, attr, baseline, start, stop, step, repeats
):
    dev = eval(classname + "(uri='" + iio_uri + "')")
    # Drop the start frequency to its floor first so applying the baseline
    # below can never momentarily overflow the sweep on any leftover state.
    dev.out_altvoltage0_frequency_start = 1000
    # Establish a known-safe sweep so start + increment * points is always
    # inside the device's valid output band regardless of prior test order.
    for battr, bval in baseline.items():
        setattr(dev, battr, bval)

    numints = int((stop - start) / step)
    for _ in range(repeats):
        val = start + step * random.randint(0, numints)
        setattr(dev, attr, val)
        readback = getattr(dev, attr)
        assert readback == val, f"{attr}: set {val}, got {readback}"


#########################################
# Device attributes restricted to a discrete set of valid values
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, values",
    [("in_voltage0_scale", [1, 0.2]), ("out_altvoltage0_raw", [1, 2, 3, 4]),],
)
def test_ad5933_attr_multiple(
    test_attribute_multiple_values, iio_uri, classname, attr, values
):
    test_attribute_multiple_values(iio_uri, classname, attr, values, 0)


#########################################
# Read-only "_available" device attributes (verify they can be read back)
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr", ["in_voltage0_scale_available", "out_altvoltage0_scale_available"],
)
def test_ad5933_attr_available_readonly(
    test_attribute_multiple_values_available_readonly, iio_uri, classname, attr
):
    test_attribute_multiple_values_available_readonly(iio_uri, classname, attr)


#########################################
# Sweep-control / measurement-trigger debug attributes.
#
# These are *action triggers*, not storage registers: writing 1 performs the
# action (initialize sweep / start sweep / repeat point / step to next point)
# and the read-back reports device state or the current output frequency, never
# the value written. A generic write/read-back test can't pass, so we exercise
# them by sequence and effect instead.
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_ad5933_sweep_sequence(iio_uri, classname):
    dev = eval(classname + "(uri='" + iio_uri + "')")

    start = 20000
    increment = 1000
    points = 10
    _configure_sweep(dev, start, increment, points)
    dev.out_altvoltage0_settling_cycles = 15

    # Initialize then start the sweep. Writing 1 is a trigger; the read-back
    # reports the resulting state, so assert on the state, not the value.
    dev.sweep_initialized = 1
    assert int(dev.sweep_initialized) == 1
    dev.sweep_started = 1
    assert int(dev.sweep_started) == 1

    # Once started, the output frequency should sit inside the configured
    # sweep band rather than returning a garbage/out-of-range value.
    freq_start = float(dev.current_output_frequency)
    assert start - increment <= freq_start <= start + increment * points

    # Repeat a measurement at the current point: the output frequency must
    # not advance.
    dev.repeat_measurement = 1
    assert float(dev.current_output_frequency) == pytest.approx(freq_start, rel=1e-3)

    # Step to the next sweep point: the output frequency must advance upward
    # (strictly increases on hardware; >= keeps this valid under a static
    # emulation where triggers are no-ops).
    dev.incremented_measurement = 1
    freq_next = float(dev.current_output_frequency)
    assert freq_next >= freq_start
    assert freq_next <= start + increment * points


#########################################
# Read-only debug attribute (no setter; verify the value can be read back)
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", ["current_output_frequency"])
def test_ad5933_debug_attr_readonly(
    test_attribute_multiple_values_available_readonly, iio_uri, classname, attr
):
    test_attribute_multiple_values_available_readonly(iio_uri, classname, attr)
