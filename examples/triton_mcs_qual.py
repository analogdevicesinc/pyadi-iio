# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Triton MCS Qualification Script

Measures delta-T0 and delta-T1 across multiple iterations to characterize
the distribution of timing deviations. Uses the statistics to compute an
optimal tracking window threshold (mean +/- 3*sigma) that avoids both
overcorrection and continuous triggering.

Optionally sweeps multiple mcs_track_decimation values to compare results.

MCS attributes are accessed via IIO debugfs (debug_attrs) on each AD9084 device.
"""

import time

import matplotlib.pyplot as plt
import numpy as np

import adi

# === Configuration ===
URI = "ip:10.44.3.70"
NUM_MEASUREMENTS = 100
NUM_CHIPS = 4

# Set to None to skip decimation sweep and just run measurements once.
# Otherwise, list of decimation values to test.
TRACK_DECIMATION_VALUES = [127, 1023, 4095, 16383, 32000]

# Set to True to apply calibration with computed thresholds after measurements
APPLY_CALIBRATION = False


def mcs_init_chip(dev, chip_idx):
    """Run MCS init and DT measurement sequence for one chip.

    Returns:
        tuple: (apollo_dt0, adf4030_dt0, apollo_dt1, adf4030_dt1,
                calc_delay, round_trip_delay, path_delay)
    """
    ctrl = dev._ctrls[chip_idx]

    # Enable sysref output
    setattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_output_enable", 1)

    # Initialize MCS (write 1 to trigger ad9088_mcs_init_cal_setup)
    ctrl.debug_attrs["mcs_init"].value = "1"

    # Measure DT0 (write 1 triggers ad9088_delta_t_measurement_set(0),
    #              read returns delta_t in femtoseconds)
    ctrl.debug_attrs["mcs_dt0_measurement"].value = "1"
    apollo_dt0 = int(ctrl.debug_attrs["mcs_dt0_measurement"].value)
    adf4030_dt0 = int(getattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_phase"))

    # Disable sysref output before DT1
    setattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_output_enable", 0)

    # Measure DT1 (write 1 triggers ad9088_delta_t_measurement_set(1),
    #              read returns delta_t in femtoseconds)
    ctrl.debug_attrs["mcs_dt1_measurement"].value = "1"
    apollo_dt1 = int(ctrl.debug_attrs["mcs_dt1_measurement"].value)
    adf4030_dt1 = int(getattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_phase"))

    # Restore (write 1 triggers ad9088_delta_t_measurement_set(2))
    ctrl.debug_attrs["mcs_dt_restore"].value = "1"

    # Compute delays
    bsync_out_period_fs = 1e15 / int(
        getattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_frequency")
    )
    calc_delay = (adf4030_dt0 - adf4030_dt1) - (apollo_dt1 - apollo_dt0)
    round_trip_delay = (calc_delay + bsync_out_period_fs) % bsync_out_period_fs
    path_delay = round_trip_delay / 2

    return (
        apollo_dt0,
        adf4030_dt0,
        apollo_dt1,
        adf4030_dt1,
        calc_delay,
        round_trip_delay,
        path_delay,
    )


def mcs_calibrate_chip(dev, chip_idx, path_delay):
    """Run MCS calibration and tracking for one chip after path delay is known."""
    ctrl = dev._ctrls[chip_idx]

    # Re-enable sysref and apply phase correction
    setattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_output_enable", 1)
    setattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_phase", -1 * path_delay)

    adf4030_phase = int(getattr(dev.adf4030, f"APOLLO_SYSREF_{chip_idx}_phase"))
    print(
        f"  Apollo{chip_idx} adf4030_phase: {adf4030_phase} fs "
        f"({adf4030_phase / 1e3:.3f} ps)"
    )

    # Run calibration (write 1 triggers adi_apollo_mcs_cal_init_run,
    #                  read returns "Passed" or "Failed")
    ctrl.debug_attrs["mcs_cal_run"].value = "1"
    print(f"  MCS Cal Status: {ctrl.debug_attrs['mcs_cal_run'].value}")

    # Init tracking (write 1 triggers ad9088_mcs_tracking_cal_setup which
    #                also configures ADF4382 en_auto_align and phase internally)
    ctrl.debug_attrs["mcs_track_cal_setup"].value = "1"

    # Foreground tracking cal (write 1 triggers adi_apollo_mcs_cal_fg_tracking_run)
    ctrl.debug_attrs["mcs_fg_track_cal_run"].value = "1"
    # Background tracking cal (write 1 starts, write 0 aborts)
    ctrl.debug_attrs["mcs_bg_track_cal_run"].value = "1"

    print(f"  MCS Init Cal Status:\n{ctrl.debug_attrs['mcs_init_cal_status'].value}")
    print(f"  MCS Track Status:\n{ctrl.debug_attrs['mcs_track_status'].value}")


def mcs_trig_sync(dev, num_chips):
    """Run the trig_sync sequence across all chips.

    Uses the 'misc' debugfs attribute (DBGFS_GENERIC) which dispatches to
    ad9088_dbg(). Value 6 = adi_apollo_clk_mcs_dyn_sync_sequence_run,
    values 1-3 = JRx/JTx phase adjust and link enable steps.
    """
    time.sleep(1)

    for i in range(num_chips):
        dev._ctrls[i].debug_attrs["misc"].value = "6"

    for step in range(1, 4):
        for i in range(num_chips):
            dev._ctrls[i].debug_attrs["misc"].value = str(step)

    for i in range(num_chips):
        dev._ctrls[i].debug_attrs["misc"].value = "6"


def print_delay_stats(label, values_fs):
    """Print statistics for a delay measurement array (in femtoseconds)."""
    arr = np.array(values_fs, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)
    mn = np.min(arr)
    mx = np.max(arr)
    print(f"  {label}:")
    print(f"    Mean:   {mean:12.0f} fs  ({mean / 1e3:9.3f} ps)")
    print(f"    Std:    {std:12.0f} fs  ({std / 1e3:9.3f} ps)")
    print(f"    Min:    {mn:12.0f} fs  ({mn / 1e3:9.3f} ps)")
    print(f"    Max:    {mx:12.0f} fs  ({mx / 1e3:9.3f} ps)")
    print(f"    Range:  {np.ptp(arr):12.0f} fs  ({np.ptp(arr) / 1e3:9.3f} ps)")
    return mean, std, mn, mx


def run_measurement_pass(dev, num_chips, decimation=None):
    """Run NUM_MEASUREMENTS DT0/DT1 measurements, analyze, and calibrate.

    Args:
        dev: Triton device handle.
        num_chips: Number of chips to measure.
        decimation: If set, write this value to mcs_track_decimation before measuring.

    Returns:
        dict: Per-chip window thresholds {chip_idx: {mean, std, low, high}}.
    """
    # Optionally set decimation
    if decimation is not None:
        for i in range(num_chips):
            dev._ctrls[i].debug_attrs["mcs_track_decimation"].value = str(decimation)

    # Storage for measurements per chip
    dt0_apollo = {i: [] for i in range(num_chips)}
    dt0_adf4030 = {i: [] for i in range(num_chips)}
    dt1_apollo = {i: [] for i in range(num_chips)}
    dt1_adf4030 = {i: [] for i in range(num_chips)}
    path_delays = {i: [] for i in range(num_chips)}

    # === Collect DT0/DT1 measurements ===
    print(f"\n--- Collecting {NUM_MEASUREMENTS} DT0/DT1 measurements ---\n")

    for run in range(NUM_MEASUREMENTS):
        for chip_idx in range(num_chips):
            (
                a_dt0,
                f_dt0,
                a_dt1,
                f_dt1,
                calc_delay,
                rt_delay,
                p_delay,
            ) = mcs_init_chip(dev, chip_idx)

            dt0_apollo[chip_idx].append(a_dt0)
            dt0_adf4030[chip_idx].append(f_dt0)
            dt1_apollo[chip_idx].append(a_dt1)
            dt1_adf4030[chip_idx].append(f_dt1)
            path_delays[chip_idx].append(p_delay)

        if (run + 1) % 10 == 0 or run == 0:
            print(f"  Run {run + 1}/{NUM_MEASUREMENTS} complete")
            for c in range(num_chips):
                n = len(path_delays[c])
                arr_dt0 = np.array(dt0_apollo[c], dtype=float)
                arr_dt1 = np.array(dt1_apollo[c], dtype=float)
                arr_pd = np.array(path_delays[c], dtype=float)
                print(
                    f"    Chip {c}: DT0 mean={np.mean(arr_dt0):10.0f} std={np.std(arr_dt0):8.0f}  "
                    f"DT1 mean={np.mean(arr_dt1):10.0f} std={np.std(arr_dt1):8.0f}  "
                    f"PD mean={np.mean(arr_pd):10.0f} std={np.std(arr_pd):8.0f} fs  "
                    f"(n={n})"
                )

    # === Analyze statistics ===
    print(f"\n{'=' * 60}")
    print("=== DT0 / DT1 Measurement Statistics ===")
    print(f"{'=' * 60}\n")

    window_thresholds = {}

    for chip_idx in range(num_chips):
        print(f"--- Apollo {chip_idx} ---")

        dt0_a_mean, dt0_a_std, dt0_a_min, dt0_a_max = print_delay_stats(
            "Apollo DT0", dt0_apollo[chip_idx]
        )
        dt0_f_mean, dt0_f_std, dt0_f_min, dt0_f_max = print_delay_stats(
            "ADF4030 DT0", dt0_adf4030[chip_idx]
        )
        dt1_a_mean, dt1_a_std, dt1_a_min, dt1_a_max = print_delay_stats(
            "Apollo DT1", dt1_apollo[chip_idx]
        )
        dt1_f_mean, dt1_f_std, dt1_f_min, dt1_f_max = print_delay_stats(
            "ADF4030 DT1", dt1_adf4030[chip_idx]
        )
        pd_mean, pd_std, pd_min, pd_max = print_delay_stats(
            "Path Delay", path_delays[chip_idx]
        )

        # Compute window threshold: mean +/- 3*sigma
        win_low = pd_mean - 3 * pd_std
        win_high = pd_mean + 3 * pd_std

        window_thresholds[chip_idx] = {
            "mean": pd_mean,
            "std": pd_std,
            "dt0_a_std": dt0_a_std,
            "dt0_a_min": dt0_a_min,
            "dt0_a_max": dt0_a_max,
            "dt0_f_std": dt0_f_std,
            "dt0_f_min": dt0_f_min,
            "dt0_f_max": dt0_f_max,
            "dt1_a_std": dt1_a_std,
            "dt1_a_min": dt1_a_min,
            "dt1_a_max": dt1_a_max,
            "dt1_f_std": dt1_f_std,
            "dt1_f_min": dt1_f_min,
            "dt1_f_max": dt1_f_max,
            "pd_std": pd_std,
            "pd_min": pd_min,
            "pd_max": pd_max,
            "low": win_low,
            "high": win_high,
        }

        print(f"\n  Tracking Window Threshold (mean +/- 3*sigma):")
        print(f"    Low:  {win_low:12.0f} fs  ({win_low / 1e3:9.3f} ps)")
        print(f"    High: {win_high:12.0f} fs  ({win_high / 1e3:9.3f} ps)")
        print(f"    Width: {6 * pd_std:11.0f} fs  ({6 * pd_std / 1e3:9.3f} ps)")
        print()

    # === Optionally apply calibration with computed thresholds ===
    if APPLY_CALIBRATION:
        print(f"\n{'=' * 60}")
        print("=== Running MCS Calibration with Computed Thresholds ===")
        print(f"{'=' * 60}\n")

        for chip_idx in range(num_chips):
            th = window_thresholds[chip_idx]
            mean_path_delay = th["mean"]

            print(f"--- Apollo {chip_idx} (path_delay={mean_path_delay:.0f} fs) ---")

            # Set tracking window using the computed threshold
            ctrl = dev._ctrls[chip_idx]
            win_value = int(3 * th["std"])
            print(
                f"  Setting mcs_track_win to {win_value} fs ({win_value / 1e3:.3f} ps)"
            )
            ctrl.debug_attrs["mcs_track_win"].value = str(win_value)

            # Run full MCS calibration using mean path delay
            mcs_calibrate_chip(dev, chip_idx, mean_path_delay)
            print()

        # Trigger sync
        print("Running trig_sync sequence...")
        mcs_trig_sync(dev, num_chips)
        print("Done.\n")
    else:
        print("\nSkipping calibration (APPLY_CALIBRATION=False)")

    return window_thresholds


def main():
    print(f"Connecting to Triton: {URI}")
    dev = adi.Triton(URI, calibration_board_attached=False)

    dev._ctx.set_timeout(30000)

    # JESD204 FSM resume
    MAX_FSM_RESUME_ATTEMPTS = 4
    for attempt in range(MAX_FSM_RESUME_ATTEMPTS):
        paused = dev.jesd204_fsm_paused
        if paused == 0:
            print("JESD204 FSM running")
            break
        print(f"JESD204 FSM resume attempt {attempt + 1}/{MAX_FSM_RESUME_ATTEMPTS}")
        dev._ctx.set_timeout(5000)
        dev.jesd204_fsm_resume = 1
        time.sleep(2)
    else:
        raise Exception(
            f"JESD204 FSM failed to resume after {MAX_FSM_RESUME_ATTEMPTS} attempts"
        )

    dev._ctx.set_timeout(5000)

    num_chips = min(NUM_CHIPS, len(dev._ctrls))
    print(f"Number of chips: {num_chips}")

    # Disable ADF4030 background serial alignment during measurements
    dev.adf4030.J46_J47_UFL_background_serial_alignment_en = 0
    print("Disabled ADF4030 background serial alignment")

    # Stop any active BG tracking cal to avoid ADF4382 corrections
    # interfering with raw DT measurements
    for i in range(num_chips):
        try:
            if int(dev._ctrls[i].debug_attrs["mcs_bg_track_cal_run"].value):
                dev._ctrls[i].debug_attrs["mcs_bg_track_cal_run"].value = "0"
                print(f"  Stopped BG tracking cal on chip {i}")
        except OSError:
            print(f"  Chip {i}: BG tracking cal stop failed (not running?), continuing")
    print("BG tracking cal check complete")

    # Run measurement passes
    if TRACK_DECIMATION_VALUES:
        all_results = {}
        for dec_val in TRACK_DECIMATION_VALUES:
            print(f"\n{'#' * 60}")
            print(f"### mcs_track_decimation = {dec_val}")
            print(f"{'#' * 60}")
            all_results[dec_val] = run_measurement_pass(
                dev, num_chips, decimation=dec_val
            )

        # Cross-decimation comparison summary - per chip
        for c in range(num_chips):
            print(f"\n{'#' * 60}")
            print(f"### Chip {c} - Decimation Sweep Summary")
            print(f"{'#' * 60}\n")

            hdr = (
                f"{'Decimation':>12s}"
                f"  {'A DT0 std':>12s}  {'A DT0 min':>12s}  {'A DT0 max':>12s}"
                f"  {'F DT0 std':>12s}  {'F DT0 min':>12s}  {'F DT0 max':>12s}"
                f"  {'A DT1 std':>12s}  {'A DT1 min':>12s}  {'A DT1 max':>12s}"
                f"  {'F DT1 std':>12s}  {'F DT1 min':>12s}  {'F DT1 max':>12s}"
                f"  {'PD std':>12s}  {'PD min':>12s}  {'PD max':>12s}"
                f"  {'3sig (ps)':>10s}"
            )
            print(hdr)
            print("-" * len(hdr))

            for dec_val in TRACK_DECIMATION_VALUES:
                r = all_results[dec_val][c]
                row = (
                    f"{dec_val:>12d}"
                    f"  {r['dt0_a_std']:>12.0f}  {r['dt0_a_min']:>12.0f}  {r['dt0_a_max']:>12.0f}"
                    f"  {r['dt0_f_std']:>12.0f}  {r['dt0_f_min']:>12.0f}  {r['dt0_f_max']:>12.0f}"
                    f"  {r['dt1_a_std']:>12.0f}  {r['dt1_a_min']:>12.0f}  {r['dt1_a_max']:>12.0f}"
                    f"  {r['dt1_f_std']:>12.0f}  {r['dt1_f_min']:>12.0f}  {r['dt1_f_max']:>12.0f}"
                    f"  {r['pd_std']:>12.0f}  {r['pd_min']:>12.0f}  {r['pd_max']:>12.0f}"
                    f"  {3 * r['pd_std'] / 1e3:>10.3f}"
                )
                print(row)

        print()
        print("A = Apollo (ad9088), F = ADF4030. All values in fs unless noted.")

        # Plot std vs tracking decimation
        dec_vals = np.array(TRACK_DECIMATION_VALUES)

        fig, axes = plt.subplots(5, 1, sharex=True, figsize=(10, 12))

        for c in range(num_chips):
            dt0_a_stds = [
                all_results[d][c]["dt0_a_std"] for d in TRACK_DECIMATION_VALUES
            ]
            dt0_f_stds = [
                all_results[d][c]["dt0_f_std"] for d in TRACK_DECIMATION_VALUES
            ]
            dt1_a_stds = [
                all_results[d][c]["dt1_a_std"] for d in TRACK_DECIMATION_VALUES
            ]
            dt1_f_stds = [
                all_results[d][c]["dt1_f_std"] for d in TRACK_DECIMATION_VALUES
            ]
            pd_stds = [all_results[d][c]["pd_std"] for d in TRACK_DECIMATION_VALUES]

            axes[0].plot(dec_vals, dt0_a_stds, "o-", label=f"Chip {c}")
            axes[1].plot(dec_vals, dt0_f_stds, "o-", label=f"Chip {c}")
            axes[2].plot(dec_vals, dt1_a_stds, "o-", label=f"Chip {c}")
            axes[3].plot(dec_vals, dt1_f_stds, "o-", label=f"Chip {c}")
            axes[4].plot(dec_vals, pd_stds, "o-", label=f"Chip {c}")

        axes[0].set_ylabel("Apollo DT0 std (fs)")
        axes[0].set_title("Measurement Std Dev vs Tracking Decimation")
        axes[1].set_ylabel("ADF4030 DT0 std (fs)")
        axes[2].set_ylabel("Apollo DT1 std (fs)")
        axes[3].set_ylabel("ADF4030 DT1 std (fs)")
        axes[4].set_ylabel("Path Delay std (fs)")
        axes[4].set_xlabel("mcs_track_decimation")

        for ax in axes:
            ax.legend()
            ax.grid(True)
            ax.set_xscale("log")

        plt.tight_layout()
        plt.show()
    else:
        run_measurement_pass(dev, num_chips)


if __name__ == "__main__":
    main()
