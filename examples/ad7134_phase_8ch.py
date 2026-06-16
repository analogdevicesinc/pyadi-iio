# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 8-channel phase-sync demo.
#
# 8-channel counterpart of ad7134_sync_demo.py.  Same before/after flow:
#   1. Capture n frames BEFORE sync  → boot/transition-time alignment
#   2. Issue DIG_IF_RESET broadcast  → aligns both chips' frame counters
#   3. Capture n frames AFTER sync   → residual alignment
#   4. Print before/after comparison + save a plot
#
# The difference vs ad7134_sync_demo.py: instead of comparing only ch0 vs ch4,
# this takes ch0 (adc_0) as the reference and reports EVERY channel relative to
# ch0, plus the four inter-chip pairs.
#
#     0..3 -> adc_0 (chip A) channels 0..3
#     4..7 -> adc_1 (chip B) channels 0..3
#
# Convention (identical to phase_shift.py):
#     phase_deg = phase(chN) - phase(ch0)
#     delay_ns  = -phi / (2*pi*f0) * 1e9
#     delay_ns > 0  => chN lags  ch0 (chN delayed)
#     delay_ns < 0  => chN leads ch0
#
# The re-lock that actually aligns the two chips is triggered by the ODR change
# on the `sampling_frequency` write below (the driver probes at 100 kHz, so a
# 1.4 MHz request is a >500 SPS transition → ASRC re-lock on both chips).
# DIG_IF_RESET (dev.sync()) then resets the frame counters on top.  The ns
# result scales with Fs, so the script uses the ACTUAL ODR the driver reports.
#
# ── Reboot pass/fail mode (--reboots N) ─────────────────────────────────────
# With --reboots N the script SSH-reboots the board N times (like
# ad7134_reboot_test.py).  Each boot starts at the 100 kHz probe default, so the
# 1.4 MHz request does a real re-lock.  After sync it classifies the boot:
#     PASS if |inter-chip mean - SYNC_BASELINE_NS| <= SYNC_TOL_NS
#     FAIL otherwise (e.g. the ~729 ns coarse slip or any out-of-spec landing)
# On a FAIL it dumps the raw 8-channel samples to a CSV in the iio_osc 8-column
# format, so the failing capture can be replayed with ad7134_phase_from_csv.py.
# At the end it prints pass/fail statistics.  No plot is produced in this mode.
# Requires passwordless SSH to root@<host> (ssh-copy-id root@<host>).
#
# Usage:
#   python3 ad7134_phase_8ch.py <uri> [target_fs] [n_captures] [--reboots N]
#
# Examples:
#   python3 ad7134_phase_8ch.py ip:10.48.65.161
#   python3 ad7134_phase_8ch.py ip:10.48.65.161 1400000
#   python3 ad7134_phase_8ch.py ip:10.48.65.161 1400000 10
#   python3 ad7134_phase_8ch.py ip:10.48.65.161 1400000 5 --reboots 20

import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

# Pass/fail (reboot mode): inter-chip after-sync delay must land within
# SYNC_TOL_NS of SYNC_BASELINE_NS, else the boot is counted as a FAIL.
SYNC_BASELINE_NS = 8.0
SYNC_TOL_NS = 10.0


def compute_phase_delay(x, y, Fs):
    """Return (f0, phase_deg, delay_ns, X, f, k_half) between x and y."""
    x = x - np.mean(x)
    y = y - np.mean(y)
    N = len(x)
    w = np.hanning(N)
    X = np.fft.fft(x * w)
    Y = np.fft.fft(y * w)
    f = np.arange(N) * (Fs / N)
    kpk = 1 + int(np.argmax(np.abs(X[1 : N // 2])))
    f0 = f[kpk]
    phi = np.angle(Y[kpk]) - np.angle(X[kpk])
    phi = np.arctan2(np.sin(phi), np.cos(phi))  # wrap to [-pi, pi]
    phase_deg = np.degrees(phi)
    delay_ns = -phi / (2 * np.pi * f0) * 1e9
    return f0, phase_deg, delay_ns, X, f, N // 2


def reboot_and_wait(host, boot_timeout=120, iiod_settle=5):
    """SSH reboot the board and wait until it is reachable again."""
    print(f"  Rebooting {host} ...", flush=True)
    subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
         f"root@{host}", "reboot"],
        check=False,
    )

    time.sleep(12)  # wait for board to go down before polling

    print("  Waiting for board to come back", end="", flush=True)
    t0 = time.monotonic()
    while time.monotonic() - t0 < boot_timeout:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
             f"root@{host}", "echo ok"],
            capture_output=True,
        )
        if result.returncode == 0:
            elapsed = time.monotonic() - t0 + 12
            print(f"\n  Board back after {elapsed:.0f} s — waiting {iiod_settle} s for iiod ...",
                  flush=True)
            time.sleep(iiod_settle)
            return
        print(".", end="", flush=True)
        time.sleep(3)

    print()
    raise TimeoutError(f"Board did not come back within {boot_timeout} s")


def measure(dev, ch_ref, Fs, n_captures):
    """Capture n_captures frames; return per-capture delay/phase arrays vs ch_ref.

    Returns (delays[n,8], phases[n,8], f0s[n], last) where last = (data, X, f, k1)
    from the final capture (for plotting / CSV dump).
    """
    delays = np.zeros((n_captures, 8))
    phases = np.zeros((n_captures, 8))
    f0s = np.zeros(n_captures)
    last = None
    for i in range(n_captures):
        data = dev.rx()
        ref = np.array(data[ch_ref], dtype=np.float64)
        for ch in range(8):
            y = np.array(data[ch], dtype=np.float64)
            f0, ph, d, X, f, k1 = compute_phase_delay(ref, y, Fs)
            delays[i, ch] = d
            phases[i, ch] = ph
            f0s[i] = f0
        last = (data, X, f, k1)
    return delays, phases, f0s, last


def capture_before_after(dev, ch_ref, Fs, n_captures):
    """Run the before / DIG_IF_RESET / after sequence.

    Returns (d_before, d_after, f0_before, f0_after, last).
    """
    d_before, _, f0_before, _ = measure(dev, ch_ref, Fs, n_captures)
    dev.rx_destroy_buffer()
    dev.sync()
    for _ in range(3):   # flush pipeline after reset
        dev.rx()
    d_after, _, f0_after, last = measure(dev, ch_ref, Fs, n_captures)
    return d_before, d_after, f0_before, f0_after, last


def inter_chip_series(delays):
    """Per-capture inter-chip delay (adc_1 mean - adc_0 mean) over channels."""
    return delays[:, 4:8].mean(axis=1) - delays[:, 0:4].mean(axis=1)


def save_fail_csv(data, boot):
    """Dump the raw 8-channel samples to an iio_osc-format CSV (for replay)."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"ad7134_sync_fail_boot{boot:03d}_{ts}.csv"
    cols = np.column_stack([np.asarray(data[ch]).astype(np.int64) for ch in range(8)])
    np.savetxt(fname, cols, delimiter=",", fmt="%d")
    return fname


def print_comparison(d_before, d_after, ch_ref, f0_before, f0_after):
    """Print the before/after per-channel and inter-chip comparison tables."""
    db_mean, db_std = d_before.mean(axis=0), d_before.std(axis=0)
    da_mean, da_std = d_after.mean(axis=0), d_after.std(axis=0)

    # ── Per-channel delay vs reference: before vs after ──────────────
    print(f"\n{'-' * 72}")
    print("  Per-channel phase/delay vs reference  (mean over captures)")
    print(f"{'-' * 72}")
    print(f"  {'ch':>3}  {'chip':>5}   {'before (ns)':>11}   "
          f"{'after (ns)':>10}   {'after std':>9}   {'delta':>8}")
    print(f"  {'-' * 3}  {'-' * 5}   {'-' * 11}   {'-' * 10}   {'-' * 9}   {'-' * 8}")
    for ch in range(8):
        chip = "adc_0" if ch < 4 else "adc_1"
        tag = "  <-- ref" if ch == ch_ref else ""
        print(f"  {ch:>3}  {chip:>5}   {db_mean[ch]:>+11.1f}   "
              f"{da_mean[ch]:>+10.1f}   {da_std[ch]:>9.1f}   "
              f"{da_mean[ch] - db_mean[ch]:>+8.1f}{tag}")

    # ── Inter-chip pairs: adc_1 chN  vs  adc_0 chN ──────────────────
    pair_b = db_mean[4:8] - db_mean[0:4]
    pair_a = da_mean[4:8] - da_mean[0:4]
    print(f"\n{'-' * 72}")
    print("  Inter-chip delay  (adc_1 chN  -  adc_0 chN):  before vs after")
    print(f"{'-' * 72}")
    print(f"  {'pair':>9}   {'before (ns)':>11}   {'after (ns)':>10}")
    print(f"  {'-' * 9}   {'-' * 11}   {'-' * 10}")
    for n in range(4):
        print(f"  ch{n + 4}-ch{n:<5}   {pair_b[n]:>+11.1f}   {pair_a[n]:>+10.1f}")
    print(f"  {'-' * 9}   {'-' * 11}   {'-' * 10}")
    print(f"  {'mean':>9}   {pair_b.mean():>+11.1f}   {pair_a.mean():>+10.1f}")
    print(f"  {'std':>9}   {pair_b.std():>11.1f}   {pair_a.std():>10.1f}")

    print(f"\n  >> Inter-chip delay (adc_0 -> adc_1): "
          f"{pair_b.mean():+.1f} ns -> {pair_a.mean():+.1f} ns "
          f"(delta {pair_a.mean() - pair_b.mean():+.1f} ns)")
    print(f"     after std {pair_a.std():.1f} ns  @ f0={f0_after.mean():.0f} Hz")
    return da_mean, da_std


def run_single(my_uri, target_fs, n_captures):
    """One capture session with full before/after tables and a plot."""
    ch_ref = 0
    buffer_size = 65534

    dev = adi.ad7134(uri=my_uri)
    dev.rx_enabled_channels = list(range(8))
    dev.rx_buffer_size = buffer_size
    dev.sampling_frequency = target_fs   # ODR change here triggers ASRC re-lock
    Fs = float(dev.sampling_frequency)

    print("=" * 72)
    print("AD7134 8-channel phase-sync demo (before / DIG_IF_RESET / after)")
    print("=" * 72)
    print(f"URI         : {my_uri}")
    print(f"Fs (target) : {target_fs} Hz ({target_fs / 1e6:.3f} MSPS)")
    print(f"Fs (actual) : {Fs:.6g} Hz ({Fs / 1e6:.4f} MSPS)")
    print(f"Filter      : {dev.filter_type}")
    print(f"Captures    : {n_captures}  (averaged per channel)")
    print(f"Reference   : ch{ch_ref}  (adc_0)")

    d_before, d_after, f0_before, f0_after, last = capture_before_after(
        dev, ch_ref, Fs, n_captures)
    print("\n  >> DIG_IF_RESET broadcast sent — frame counters aligned")

    da_mean, da_std = print_comparison(
        d_before, d_after, ch_ref, f0_before, f0_after)
    print("=" * 72)

    # ── Plot: all 8 channels (after) + per-channel delay bar ─────────
    data, X, f, k1 = last
    N = data[ch_ref].shape[0]
    t = np.arange(N) / Fs
    n_plot = min(N, 2048)
    pair_a = da_mean[4:8] - da_mean[0:4]

    fig, axs = plt.subplots(2, 1, figsize=(11, 9))
    fig.suptitle(f"AD7134 8-channel phase-sync — inter-chip after {pair_a.mean():+.1f} ns "
                 f"@ f0={f0_after.mean():.0f} Hz, Fs={Fs / 1e6:.4f} MSPS")

    for ch in range(8):
        y = np.array(data[ch], dtype=np.float64)
        y = y - np.mean(y)
        chip = "adc_0" if ch < 4 else "adc_1"
        style = "-" if ch < 4 else "--"
        axs[0].plot(t[:n_plot] * 1e3, y[:n_plot], style,
                    label=f"ch{ch} ({chip})", alpha=0.85)
    axs[0].set_xlabel("Time (ms)")
    axs[0].set_ylabel("Amplitude (counts)")
    axs[0].set_title("Time-domain after sync (DC-removed, all 8 channels)")
    axs[0].legend(ncol=4, fontsize=8)
    axs[0].grid(True)

    colors = ["C0"] * 4 + ["C1"] * 4
    ypos = np.arange(8)
    axs[1].barh(ypos, da_mean, xerr=da_std, color=colors)
    axs[1].axvline(0, color="k", lw=0.8)
    axs[1].set_yticks(ypos)
    axs[1].set_yticklabels([f"ch{c}" for c in range(8)])
    axs[1].invert_yaxis()  # ch0 at top
    axs[1].set_xlabel(f"delay vs ch{ch_ref} (ns)")
    axs[1].set_title("Per-channel delay relative to reference, after sync "
                     "(blue=adc_0, orange=adc_1)")
    axs[1].grid(True, axis="x")
    for c, v in enumerate(da_mean):
        axs[1].text(v, c, f" {v:+.1f}", va="center",
                    ha="left" if v >= 0 else "right", fontsize=8)

    plt.tight_layout()
    out_png = "ad7134_phase_8ch.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved -> {out_png}")
    plt.show(block=False)
    plt.pause(5)
    plt.close("all")

    del dev


def run_reboot_loop(my_uri, target_fs, n_captures, n_reboots):
    """Reboot the board n_reboots times; classify each boot pass/fail."""
    if not my_uri.startswith("ip:"):
        print("ERROR: --reboots requires an 'ip:' URI for SSH reboot support.")
        sys.exit(1)
    host = my_uri[3:]
    ch_ref = 0
    buffer_size = 65534

    print("=" * 72)
    print("AD7134 8-channel reboot pass/fail sync test")
    print("=" * 72)
    print(f"URI         : {my_uri}")
    print(f"Reboots     : {n_reboots}")
    print(f"Target ODR  : {target_fs} Hz ({target_fs / 1e6:.3f} MSPS)")
    print(f"Captures    : {n_captures} before + {n_captures} after per boot")
    print(f"PASS window : inter-chip within {SYNC_BASELINE_NS:+.0f} +/- {SYNC_TOL_NS:.0f} ns")
    print("=" * 72)

    results = []   # (boot, inter_before, inter_after, inter_std, is_pass, fname)

    for boot in range(1, n_reboots + 1):
        print(f"\n{'-' * 72}")
        print(f"Boot {boot}/{n_reboots}")
        print(f"{'-' * 72}")

        reboot_and_wait(host)

        dev = adi.ad7134(uri=my_uri)
        dev.rx_enabled_channels = list(range(8))
        dev.rx_buffer_size = buffer_size
        dev.sampling_frequency = target_fs   # 100k(probe) -> target = re-lock
        Fs = float(dev.sampling_frequency)
        print(f"  Fs = {Fs:.6g} Hz")

        d_before, d_after, _, _, last = capture_before_after(
            dev, ch_ref, Fs, n_captures)

        inter_before = float(inter_chip_series(d_before).mean())
        after_series = inter_chip_series(d_after)
        inter_after = float(after_series.mean())
        inter_std = float(after_series.std())

        is_pass = abs(inter_after - SYNC_BASELINE_NS) <= SYNC_TOL_NS
        fname = ""
        if not is_pass:
            fname = save_fail_csv(last[0], boot)

        verdict = "PASS" if is_pass else "FAIL"
        extra = "" if is_pass else f"  -> saved {fname}"
        print(f"  Boot {boot}: before={inter_before:+.1f} ns  "
              f"after={inter_after:+.1f} ns (std={inter_std:.1f})  "
              f"[{verdict}]{extra}")

        results.append((boot, inter_before, inter_after, inter_std, is_pass, fname))
        del dev
        if boot < n_reboots:
            time.sleep(3)

    # ── Per-boot table ───────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print("  PER-BOOT")
    print(f"{'=' * 78}")
    print(f"  {'Boot':>5}   {'Before (ns)':>11}   {'After (ns)':>10}   "
          f"{'Std':>6}   {'Result':>6}   {'Saved CSV':<28}")
    print(f"  {'-' * 5}   {'-' * 11}   {'-' * 10}   {'-' * 6}   {'-' * 6}   {'-' * 28}")
    for boot, ib, ia, istd, ok, fn in results:
        print(f"  {boot:>5}   {ib:>+11.1f}   {ia:>+10.1f}   {istd:>6.1f}   "
              f"{'PASS' if ok else 'FAIL':>6}   {fn:<28}")

    # ── Statistics ───────────────────────────────────────────────────
    n_pass = sum(1 for r in results if r[4])
    n_fail = len(results) - n_pass
    afters = [r[2] for r in results]
    print(f"\n{'=' * 78}")
    print("  STATISTICS")
    print(f"{'=' * 78}")
    print(f"  Boots     : {len(results)}")
    print(f"  PASS      : {n_pass}  ({100.0 * n_pass / len(results):.1f} %)")
    print(f"  FAIL      : {n_fail}  ({100.0 * n_fail / len(results):.1f} %)")
    if afters:
        print(f"  after ns  : mean {np.mean(afters):+.1f}  std {np.std(afters):.1f}  "
              f"min {np.min(afters):+.1f}  max {np.max(afters):+.1f}")
    if n_fail:
        print("  Saved fail captures (replay with ad7134_phase_from_csv.py):")
        for r in results:
            if not r[4]:
                print(f"    boot {r[0]}: {r[5]}  (inter-chip {r[2]:+.1f} ns)")
    print(f"{'=' * 78}")


def main():
    argv = sys.argv[1:]
    n_reboots = 0
    if "--reboots" in argv:
        i = argv.index("--reboots")
        n_reboots = int(argv[i + 1])
        del argv[i:i + 2]

    my_uri = argv[0] if len(argv) >= 1 else "ip:analog.local"
    target_fs = int(argv[1]) if len(argv) >= 2 else 1400000
    n_captures = int(argv[2]) if len(argv) >= 3 else 5

    if n_reboots > 0:
        run_reboot_loop(my_uri, target_fs, n_captures, n_reboots)
    else:
        run_single(my_uri, target_fs, n_captures)


if __name__ == "__main__":
    main()
