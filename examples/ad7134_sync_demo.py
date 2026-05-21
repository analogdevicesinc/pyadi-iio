# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 phase-sync demo.
#
# Demonstrates inter-chip synchronisation on two AD4134 ADCs:
#   1. Reload driver (rmmod + modprobe) for a clean hardware startup
#   2. Capture 5 frames BEFORE sync  → shows random boot-time misalignment
#   3. Issue DIG_IF_RESET broadcast  → aligns both chips' frame counters
#   4. Capture 5 frames AFTER sync   → shows residual delay after alignment
#   5. Print before/after comparison table and save a plot

import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi


def reload_driver(uri):
    """Reload the ad4134 kernel driver for a clean, synchronised startup.

    modprobe blocks until the full init sequence completes (~12 s):
    hardware reset → ODR start → simultaneous PDN cycle → PLL lock wait.
    """
    t0 = time.monotonic()
    if uri.startswith("ip:"):
        host = uri[3:]
        print(f"Reloading ad4134 driver on {host} ...")
        subprocess.run(
            ["ssh", f"root@{host}", "rmmod ad4134 2>/dev/null; modprobe ad4134"],
            check=True,
        )
    else:
        print("Reloading ad4134 driver locally ...")
        subprocess.run(["rmmod", "ad4134"], check=False)
        subprocess.run(["modprobe", "ad4134"], check=True)
    time.sleep(2)  # let iiod enumerate the new IIO devices
    elapsed = time.monotonic() - t0
    print(f"Driver reloaded in {elapsed:.1f} s.")


def compute_phase_delay(x, y, Fs):
    """Return (f0, phase_deg, delay_ns) between signals x and y."""
    x = x - np.mean(x)
    y = y - np.mean(y)
    N = len(x)
    w = np.hanning(N)
    X = np.fft.fft(x * w)
    Y = np.fft.fft(y * w)
    f = np.arange(N) * (Fs / N)
    kpk = 1 + np.argmax(np.abs(X[1 : N // 2]))
    f0 = f[kpk]
    phi = np.angle(Y[kpk]) - np.angle(X[kpk])
    phi = np.arctan2(np.sin(phi), np.cos(phi))
    phase_deg = np.degrees(phi)
    delay_ns = -phi / (2 * np.pi * f0) * 1e9
    return f0, phase_deg, delay_ns, X, f, N // 2


def main():
    my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    ch_a = 0        # reference  (adc_0, chip A)
    ch_b = 4        # compare    (adc_1, chip B)
    buffer_size = 65534
    n_captures = 5

    print("=" * 60)
    print("AD7134 Phase-Sync Demo")
    print("=" * 60)
    print(f"URI: {my_uri}")

    # ── Step 1: clean hardware startup ──────────────────────────────
    reload_driver(my_uri)

    dev = adi.ad7134(uri=my_uri)
    dev.rx_enabled_channels = list(range(8))
    dev.rx_buffer_size = buffer_size

    Fs = float(dev.sampling_frequency)
    print(f"\nFs       = {Fs:.6g} Hz ({Fs / 1e6:.3f} MSPS)")
    print(f"Filter   = {dev.filter_type}")
    print(f"Channels = ch{ch_a} (adc_0)  vs  ch{ch_b} (adc_1)\n")

    # ── Step 2: captures BEFORE sync ────────────────────────────────
    print(f"--- BEFORE sync ({n_captures} captures) ---")
    results_before = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)
        f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
        results_before.append(delay_ns)
        print(f"  [{i + 1}]  f0 = {f0:.1f} Hz   phase = {phase_deg:+.3f} deg   delay = {delay_ns:+.1f} ns")

    # ── Step 3: sync ─────────────────────────────────────────────────
    dev.rx_destroy_buffer()
    dev.sync()
    for _ in range(3):   # flush pipeline after reset
        dev.rx()
    print("\n  >> DIG_IF_RESET broadcast sent — frame counters aligned\n")

    # ── Step 4: captures AFTER sync ──────────────────────────────────
    print(f"--- AFTER sync ({n_captures} captures) ---")
    results_after = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)
        f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
        results_after.append(delay_ns)
        print(f"  [{i + 1}]  f0 = {f0:.1f} Hz   phase = {phase_deg:+.3f} deg   delay = {delay_ns:+.1f} ns")

    # ── Step 5: summary table ────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  {'Capture':>7}   {'Before sync (ns)':>16}   {'After sync (ns)':>15}")
    print(f"  {'-' * 7}   {'-' * 16}   {'-' * 15}")
    for i, (b, a) in enumerate(zip(results_before, results_after)):
        print(f"  {i + 1:>7}   {b:>+16.1f}   {a:>+15.1f}")
    print(f"  {'-' * 7}   {'-' * 16}   {'-' * 15}")
    print(f"  {'mean':>7}   {np.mean(results_before):>+16.1f}   {np.mean(results_after):>+15.1f}")
    print(f"  {'std':>7}   {np.std(results_before):>16.1f}   {np.std(results_after):>15.1f}")
    print(f"{'=' * 60}")
    print(f"\n  Sync effect: {np.mean(results_before):+.1f} ns → {np.mean(results_after):+.1f} ns"
          f"   (Δ = {np.mean(results_after) - np.mean(results_before):+.1f} ns)")

    # ── Step 6: plot last capture ────────────────────────────────────
    N = len(x)
    t = np.arange(N) / Fs
    n_plot = min(N, 2048)

    fig, axs = plt.subplots(3, 1, figsize=(10, 9))
    fig.suptitle(f"AD7134 Phase-Sync Demo — after sync: {delay_ns:+.1f} ns")

    axs[0].plot(t[:n_plot] * 1e3, x[:n_plot], label=f"ch{ch_a} (adc_0)")
    axs[0].plot(t[:n_plot] * 1e3, y[:n_plot], label=f"ch{ch_b} (adc_1)", alpha=0.8)
    axs[0].set_xlabel("Time (ms)")
    axs[0].set_ylabel("Amplitude (counts)")
    axs[0].set_title("Time-domain (first 2048 samples, after sync)")
    axs[0].legend()
    axs[0].grid(True)

    axs[1].plot(x[:n_plot], y[:n_plot], "k.", markersize=1)
    axs[1].set_aspect("equal")
    axs[1].set_xlabel(f"ch{ch_a} (adc_0)")
    axs[1].set_ylabel(f"ch{ch_b} (adc_1)")
    axs[1].set_title(f"X-Y (Lissajous) — phase = {phase_deg:+.4f} deg,  delay = {delay_ns:+.1f} ns")
    axs[1].grid(True)

    axs[2].plot(f[:k1], 20 * np.log10(np.abs(X[:k1]) + np.finfo(float).tiny))
    axs[2].set_xlabel("Frequency (Hz)")
    axs[2].set_ylabel("|X(f)| (dB)")
    axs[2].set_title(f"Spectrum  f0 = {f0:.1f} Hz")
    axs[2].grid(True)

    plt.tight_layout()
    plt.savefig("ad7134_sync_demo.png", dpi=150, bbox_inches="tight")
    print("\nPlot saved → ad7134_sync_demo.png")
    plt.show()

    del dev


if __name__ == "__main__":
    main()
