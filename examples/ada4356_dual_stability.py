# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Dual ADA4356 — Long-term offset stability monitor.

Captures the delay between the two ADC boards at regular intervals and
builds a live table showing whether the sample offset is stable over time.

Usage:
  python3 ada4356_dual_stability.py ip:192.168.2.1
  python3 ada4356_dual_stability.py ip:192.168.2.1 300 3600 65536
  #                                                 ^   ^     ^
  #                                          interval  total  buffer
"""

import csv
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

import adi

uri            = sys.argv[1] if len(sys.argv) > 1 else "ip:192.168.2.1"
interval_s     = int(sys.argv[2]) if len(sys.argv) > 2 else 300    # 5 min
duration_s     = int(sys.argv[3]) if len(sys.argv) > 3 else 3600   # 1 hour
buffer_samples = int(sys.argv[4]) if len(sys.argv) > 4 else 65536

TDD_CLOCK_HZ = 125_000_000
TDD_ON_BASE  = 100
TDD_OFF_BASE = 200

ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path     = f"/tmp/ada4356_stability_{ts}.csv"
plot_path    = f"/tmp/ada4356_stability_{ts}.png"

# ── measurement ───────────────────────────────────────────────────────────────

def measure(dev, fs):
    data0, data1 = dev.rx_synced()
    N  = min(len(data0), len(data1))
    d0 = data0[:N].astype(np.float64) - np.mean(data0[:N])
    d1 = data1[:N].astype(np.float64) - np.mean(data1[:N])

    window    = np.hanning(N)
    D0        = np.fft.rfft(d0 * window)
    D1        = np.fft.rfft(d1 * window)
    freq_axis = np.fft.rfftfreq(N, d=1.0 / fs)
    fund_bin  = np.argmax(np.abs(D0[1:])) + 1
    fund_freq = freq_axis[fund_bin]

    # SNR: peak bin vs median of the spectrum
    snr_db = 20 * np.log10(np.abs(D0[fund_bin]) / (np.median(np.abs(D0)) + 1e-12))

    phase0     = np.angle(D0[fund_bin], deg=True)
    phase1     = np.angle(D1[fund_bin], deg=True)
    phase_diff = (phase1 - phase0 + 180) % 360 - 180

    delay_samp = phase_diff / 360.0 * (fs / fund_freq)
    delay_ns   = delay_samp / fs * 1e9

    return dict(
        fund_freq_hz  = fund_freq,
        phase0_deg    = phase0,
        phase1_deg    = phase1,
        phase_diff_deg= phase_diff,
        delay_samples = delay_samp,
        delay_ns      = delay_ns,
        snr_db        = snr_db,
    )

# ── connect ───────────────────────────────────────────────────────────────────

dev = adi.ada4356_dual(uri=uri)
dev.board0.rx_enabled_channels = [0]
dev.board1.rx_enabled_channels = [0]
dev.board0.rx_buffer_size      = buffer_samples
dev.board1.rx_buffer_size      = buffer_samples
fs = float(dev.board0.sampling_frequency)

# Arm TDD once — keep running for the entire session
tdd = dev.tdd
tdd.enable               = False
tdd.burst_count          = 0
tdd.frame_length_raw     = TDD_CLOCK_HZ
tdd.channel[1].on_raw    = TDD_ON_BASE
tdd.channel[1].off_raw   = TDD_OFF_BASE
tdd.channel[1].enable    = True
tdd.channel[2].on_raw    = TDD_ON_BASE
tdd.channel[2].off_raw   = TDD_OFF_BASE
tdd.channel[2].enable    = True
tdd.enable               = True
try:
    tdd.sync_soft = True
except Exception:
    pass

time.sleep(0.3)

# ── CSV init ──────────────────────────────────────────────────────────────────

CSV_FIELDS = [
    "capture", "timestamp", "elapsed_s", "elapsed_min",
    "delay_samples", "delay_ns",
    "phase0_deg", "phase1_deg", "phase_diff_deg",
    "fund_freq_hz", "snr_db",
]

with open(csv_path, "w", newline="") as f:
    csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

# ── table header ──────────────────────────────────────────────────────────────

n_captures = duration_s // interval_s + 1

COL = (
    f"{'#':>4}  {'Time':>8}  {'Elaps':>6}  "
    f"{'Delay(samp)':>12}  {'Delay(ns)':>10}  "
    f"{'mean±std(samp)':>20}  "
    f"{'B0°':>8}  {'B1°':>8}  {'Δ°':>7}  "
    f"{'Fund kHz':>9}  {'SNR dB':>7}"
)
SEP = "─" * len(COL)

print(f"\nStability monitor — interval {interval_s}s, duration {duration_s}s, "
      f"{n_captures} captures")
print(f"fs = {fs/1e6:.3f} MHz  buffer = {buffer_samples} samp "
      f"({buffer_samples/fs*1e3:.1f} ms)  1 samp = {1/fs*1e9:.2f} ns")
print(f"CSV  → {csv_path}")
print(f"Plot → {plot_path}")
print(SEP)
print(COL)
print(SEP)

# ── main loop ─────────────────────────────────────────────────────────────────

results    = []
start_time = time.time()

try:
    for i in range(n_captures):
        now        = datetime.now()
        elapsed_s  = time.time() - start_time
        elapsed_m  = elapsed_s / 60.0

        try:
            m = measure(dev, fs)
        except Exception as exc:
            print(f"{i+1:>4}  {now.strftime('%H:%M:%S')}  {elapsed_m:>5.1f}m  "
                  f"ERROR: {exc}")
            # still wait for next slot
            next_t = start_time + (i + 1) * interval_s
            wait   = next_t - time.time()
            if wait > 0:
                time.sleep(wait)
            continue

        row = dict(
            capture      = i + 1,
            timestamp    = now.strftime("%H:%M:%S"),
            elapsed_s    = round(elapsed_s, 1),
            elapsed_min  = round(elapsed_m, 3),
            **m,
        )
        results.append(row)

        # running stats
        delays    = [r["delay_samples"] for r in results]
        run_mean  = np.mean(delays)
        run_std   = np.std(delays) if len(delays) > 1 else 0.0
        stats_str = f"{run_mean:+.4f}±{run_std:.4f}"

        # repeat header every 15 rows
        if i > 0 and i % 15 == 0:
            print(SEP)
            print(COL)
            print(SEP)

        print(
            f"{i+1:>4}  {row['timestamp']:>8}  {elapsed_m:>5.1f}m  "
            f"{m['delay_samples']:>+12.4f}  {m['delay_ns']:>+10.3f}  "
            f"{stats_str:>20}  "
            f"{m['phase0_deg']:>+8.2f}  {m['phase1_deg']:>+8.2f}  "
            f"{m['phase_diff_deg']:>+7.3f}  "
            f"{m['fund_freq_hz']/1e3:>9.3f}  {m['snr_db']:>7.1f}"
        )

        # save row to CSV immediately (safe against interruption)
        with open(csv_path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(
                {k: row[k] for k in CSV_FIELDS}
            )

        # sleep until next scheduled capture
        if i < n_captures - 1:
            next_t = start_time + (i + 1) * interval_s
            wait   = next_t - time.time()
            if wait > 0:
                time.sleep(wait)

except KeyboardInterrupt:
    print(f"\n[Stopped by user after {len(results)} captures]")

finally:
    # ── summary ───────────────────────────────────────────────────────────────

    if not results:
        print("No data collected.")
        dev.board0.rx_destroy_buffer()
        dev.board1.rx_destroy_buffer()
        sys.exit(0)

    delays    = np.array([r["delay_samples"] for r in results])
    delays_ns = delays / fs * 1e9

    print(SEP)
    print(f"\nStability report — {len(results)} captures over "
          f"{results[-1]['elapsed_min']:.1f} minutes\n")
    print(f"  {'Metric':<28}  {'Samples':>10}  {'Nanoseconds':>12}")
    print(f"  {'':<28}  {'----------':>10}  {'------------':>12}")
    print(f"  {'Mean offset (B1−B0)':<28}  {np.mean(delays):>+10.4f}  "
          f"{np.mean(delays_ns):>+12.3f}")
    print(f"  {'Std (1σ — shot-to-shot)':<28}  {np.std(delays):>10.4f}  "
          f"{np.std(delays_ns):>12.3f}")
    print(f"  {'Min':<28}  {np.min(delays):>+10.4f}  {np.min(delays_ns):>+12.3f}")
    print(f"  {'Max':<28}  {np.max(delays):>+10.4f}  {np.max(delays_ns):>+12.3f}")
    print(f"  {'Peak-to-peak':<28}  {np.ptp(delays):>10.4f}  {np.ptp(delays_ns):>12.3f}")
    print(f"  {'3σ stability band':<28}  {3*np.std(delays):>10.4f}  "
          f"{3*np.std(delays_ns):>12.3f}")

    # ── plot ──────────────────────────────────────────────────────────────────

    elapsed_min = [r["elapsed_min"] for r in results]
    phases0     = [r["phase0_deg"]  for r in results]
    phases1     = [r["phase1_deg"]  for r in results]
    mean_d      = float(np.mean(delays))
    std_d       = float(np.std(delays))

    fig, axes = plt.subplots(3, 1, figsize=(12, 11))

    # ── panel 1: delay vs time (primary) ─────────────────────────────────────
    axes[0].plot(elapsed_min, delays, "o-", color="tab:blue", markersize=6,
                 linewidth=1.5, label="Delay B1−B0")
    axes[0].axhline(mean_d, color="black", linestyle="--", linewidth=1.2,
                    label=f"mean = {mean_d:+.4f} samp ({mean_d/fs*1e9:+.3f} ns)")
    axes[0].axhspan(mean_d - std_d,     mean_d + std_d,     alpha=0.18,
                    color="tab:blue", label=f"±1σ = {std_d:.4f} samp")
    axes[0].axhspan(mean_d - 3 * std_d, mean_d + 3 * std_d, alpha=0.07,
                    color="tab:blue", label=f"±3σ = {3*std_d:.4f} samp")
    axes[0].set_xlabel("Elapsed time (min)")
    axes[0].set_ylabel("Delay B1−B0 (samples)")
    axes[0].set_title(
        f"Sample offset stability — "
        f"mean = {mean_d:+.4f} samp ({mean_d/fs*1e9:+.3f} ns),  "
        f"std = {std_d:.4f} samp ({std_d/fs*1e9:.3f} ns),  "
        f"pk-pk = {np.ptp(delays):.4f} samp"
    )
    axes[0].legend(fontsize=8, loc="upper right")
    axes[0].grid(True, alpha=0.3)

    # ── panel 2: absolute phases ──────────────────────────────────────────────
    axes[1].plot(elapsed_min, phases0, "o-", color="tab:blue",   markersize=5,
                 label="Board 0")
    axes[1].plot(elapsed_min, phases1, "o-", color="tab:orange", markersize=5,
                 alpha=0.85, label="Board 1")
    axes[1].set_xlabel("Elapsed time (min)")
    axes[1].set_ylabel("Absolute phase (°)")
    axes[1].set_title("Absolute phase per board vs time "
                      "(common drift = clock drift, differential = real desync)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # ── panel 3: histogram of delays ─────────────────────────────────────────
    nbins = max(7, len(delays) // 3)
    axes[2].hist(delays, bins=nbins, color="tab:blue", alpha=0.75, edgecolor="white")
    axes[2].axvline(mean_d,           color="black", linestyle="--",
                    label=f"mean = {mean_d:+.4f} samp")
    axes[2].axvline(mean_d - std_d,   color="gray",  linestyle=":",
                    label=f"±1σ = {std_d:.4f} samp")
    axes[2].axvline(mean_d + std_d,   color="gray",  linestyle=":")
    axes[2].axvline(mean_d - 3*std_d, color="silver", linestyle=":")
    axes[2].axvline(mean_d + 3*std_d, color="silver", linestyle=":",
                    label=f"±3σ = {3*std_d:.4f} samp")
    axes[2].set_xlabel("Delay B1−B0 (samples)")
    axes[2].set_ylabel("Count")
    axes[2].set_title("Distribution of measured offset")
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)

    print(f"\nPlot saved: {plot_path}")
    print(f"CSV  saved: {csv_path}")

    dev.board0.rx_destroy_buffer()
    dev.board1.rx_destroy_buffer()
