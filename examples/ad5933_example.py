# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
import math
import time

from adi.ad5933 import ad5933


def run_sweep(dev, single=False):
    dev.sweep_initialized = 1
    dev.sweep_started = 1
    # single=True reads a single point (real/imag) instead of the full sweep.
    if single:
        return [dev.real.raw], [dev.imag.raw]
    return dev.rx()


def print_sweep(real, imag, dev, gain_factors, wire_mode, pass_num=None):
    start = dev.out_altvoltage0_frequency_start
    increment = dev.out_altvoltage0_frequency_increment

    header = "Sweep results"
    if pass_num is not None:
        header += " (pass " + str(pass_num) + ", Ctrl+C to stop)"
    print()
    print(header)

    for i, (re, im) in enumerate(zip(real, imag)):
        freq = start + i * increment
        mag = math.hypot(float(re), float(im))
        phase_deg = math.degrees(math.atan2(float(im), float(re)))
        line = (
            "  f="
            + str(freq)
            + " Hz  real="
            + str(re)
            + "  imag="
            + str(im)
            + "  |M|="
            + str(round(mag, 2))
            + "  phase="
            + str(round(phase_deg, 2))
            + " deg"
        )
        if gain_factors:
            gf = gain_factors[i] if i < len(gain_factors) else gain_factors[-1]
            if wire_mode == "2-wire":
                impedance = 1.0 / (gf * mag) if (gf and mag) else float("inf")
            else:
                impedance = gf * mag
            line += "  |Z|=" + str(round(impedance, 3)) + " ohm"

        if abs(float(re)) < 1000 and abs(float(im)) < 1000:
            line += " *(WARNING: Signal is too small. Increase gain.)"
        if abs(float(re)) > 16000 or abs(float(im)) > 16000:
            line += " *(WARNING: ADC saturation. Decrease gain.)"
        print(line)


def plot_sweep(real, imag, dev, gain_factors, wire_mode):
    # Bode-style view of the sweep: magnitude, phase, and (when calibrated)
    # impedance, each on its own panel sharing the frequency x-axis. Two
    # measures of different scale never share one y-axis.
    import matplotlib.pyplot as plt
    import numpy as np

    start = dev.out_altvoltage0_frequency_start
    increment = dev.out_altvoltage0_frequency_increment

    freqs = []
    mags = []
    phases = []
    impedances = []
    for i, (re, im) in enumerate(zip(real, imag)):
        freqs.append((start + i * increment) / 1000.0)  # kHz
        mag = math.hypot(float(re), float(im))
        mags.append(mag)
        phases.append(math.degrees(math.atan2(float(im), float(re))))
        if gain_factors:
            gf = gain_factors[i] if i < len(gain_factors) else gain_factors[-1]
            if wire_mode == "2-wire":
                impedances.append(1.0 / (gf * mag) if (gf and mag) else float("nan"))
            else:
                impedances.append(gf * mag)

    # Validated categorical hues (dataviz palette): one entity per panel.
    blue, orange, aqua, red = "#2a78d6", "#eb6834", "#1baf7a", "#f10101"
    grid, muted = "#e1e0d9", "#898781"

    panels = [("Magnitude |M| (code)", mags, blue)]
    if impedances:
        panels.append(("Impedance |Z| (ohm)", impedances, aqua))
    phases_unwrapped = np.unwrap(p=phases, discont=180, axis=-1, period=360)
    panels.append(("Phase (deg)", phases, orange))
    panels.append(("Phase Unwrapped (deg)", phases_unwrapped, red))

    fig, axes = plt.subplots(
        len(panels), 1, sharex=True, figsize=(8, 2.4 * len(panels))
    )
    if len(panels) == 1:
        axes = [axes]

    for ax, (label, values, color) in zip(axes, panels):
        ax.plot(freqs, values, color=color, linewidth=1.5, marker="o", markersize=5)
        ax.set_ylabel(label)
        ax.grid(True, color=grid, linewidth=0.8)
        ax.tick_params(colors=muted)
        for spine in ax.spines.values():
            spine.set_color(grid)

    axes[0].set_title("AD5933 frequency sweep")
    axes[-1].set_xlabel("Frequency (kHz)")
    fig.tight_layout()
    plt.show()
    plt.close(fig)


def measure_gain_factors(dev, calibration_impedance, wire_mode, single=False):
    # Per-point gain factor from a known reference impedance:
    #   2-wire: GF = 1 / (|M_cal| * Z_cal),  Z = 1 / (GF * |M|)
    #   4-wire: GF = Z_cal / |M_cal|,        Z = GF * |M|
    cal_real, cal_imag = run_sweep(dev, single=single)
    gfs = []
    for re, im in zip(cal_real, cal_imag):
        magnitude = math.hypot(float(re), float(im))
        if wire_mode == "2-wire":
            gfs.append(1.0 / (magnitude * calibration_impedance) if magnitude else 0.0)
        else:
            gfs.append((calibration_impedance / magnitude) if magnitude else 0.0)
    return gfs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AD5933 frequency sweep with impedance calibration"
    )
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:/dev/ttyACM0,115200,8n1",
        help="IIO context URI. Use 'ip:<address>' for Ethernet"
        " or 'serial:<port>,<baud>,8n1' for USB serial.",
    )
    args = parser.parse_args()

    with ad5933(uri=args.uri) as dev:
        # Output excitation amplitude: writing 3 selects excitation Range 3
        # (0.4 V p-p). See dev.out_altvoltage0_scale_available for the codes.
        #
        # Table 17. Output Series Resistance (R_OUT) vs. Excitation Range
        #   Parameter | Value (Typ) | Output Series Resistance Value
        #   Range 1   | 2 V p-p     | 200 ohm typ
        #   Range 2   | 1 V p-p     | 2.4 kohm typ
        #   Range 3   | 0.4 V p-p   | 1.0 kohm typ
        #   Range 4   | 0.2 V p-p   | 600 ohm typ
        dev.out_altvoltage0_raw = 3
        # Input PGA scale applied to the return signal: 1 (x1) or 0.2 (x5)
        # (see dev.in_voltage0_scale_available).
        dev.in_voltage0_scale = 1
        dev.out_altvoltage0_frequency_start = 10000  # Sweep start frequency, Hz
        dev.out_altvoltage0_frequency_points = 20  # Number of points in the sweep
        dev.out_altvoltage0_frequency_increment = 1000  # Step between points, Hz
        # Output cycles to settle before measuring (0-2044).
        dev.out_altvoltage0_settling_cycles = 50

        wire_mode = "2-wire"  # 2-wire or 4-wire
        calibration_impedance = 500

        print("AD5933 configuration")
        print(
            "  Start frequency:     " + str(dev.out_altvoltage0_frequency_start) + " Hz"
        )
        print(
            "  Frequency increment: "
            + str(dev.out_altvoltage0_frequency_increment)
            + " Hz"
        )
        print("  Frequency points:    " + str(dev.out_altvoltage0_frequency_points))
        print("  Output amplitude:    " + str(dev.out_altvoltage0_raw))
        print("  Input PGA scale:     " + str(dev.in_voltage0_scale))
        print("  Wire mode:           " + str(wire_mode))

        temp_c = dev.temp.raw * dev.temp.scale
        print("  Die temperature:     " + str(round(temp_c, 3)) + " C")

        dev.rx_enabled_channels = [0, 1]
        dev.rx_buffer_size = dev.out_altvoltage0_frequency_points + 1

        print()
        print(
            "Connect the "
            + str(calibration_impedance)
            + " ohm reference impedance."
        )
        input("Press Enter to start calibration...")
        time.sleep(1.0)  # Warm-up: let the device settle before calibrating.

        gain_factors = measure_gain_factors(dev, calibration_impedance, wire_mode)

        while True:
            print()
            input("Connect the device under test and press Enter to start the sweep...")
            time.sleep(1.0)
            print()
            real, imag = run_sweep(dev)
            print_sweep(real, imag, dev, gain_factors, wire_mode)

            # Plot the most recent sweep.
            if real is not None:
                print("  NOTE: Close plots to measure again.")
                plot_sweep(real, imag, dev, gain_factors, wire_mode)
