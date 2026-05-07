# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 synchronization stability test.
# Captures data directly via pyadi-iio (no iio_osc / CSV needed).
#
# Test flow:
#   1. PDN reset (full power-down of both AD7134 chips)
#   2. Reconfigure registers, set Fs = 1.496 MHz, filter = SINC6
#   3. Capture 5 times WITHOUT sync  (expect broken/random phase)
#   4. Call sync (DIG_IF_RESET broadcast to both chips)
#   5. Capture 5 times WITH sync     (expect stable phase)
#   6. Print summary table
#
# Convention:
#   phase_deg = phase(y) - phase(x)
#   delay_ns  = -phase_rad / (2*pi*f0) * 1e9
#   delay_ns > 0  => y lags x (y delayed)
#   delay_ns < 0  => y leads x

import sys

import matplotlib.pyplot as plt
import numpy as np

import adi


def compute_phase_delay(x, y, Fs):
    """Compute phase difference and time delay between two signals.

    Returns (f0, phase_deg, delay_ns, X, f, k1) where f0 is the dominant
    frequency.  Algorithm is identical to phase_shift.py / phase_shift.m.
    """
    x = x - np.nanmean(x)
    y = y - np.nanmean(y)

    N = len(x)

    ## ===== WINDOW (reduces leakage if not integer cycles) =====
    w = np.hanning(N)
    xw = x * w
    yw = y * w

    ## ===== FFT + DOMINANT TONE =====
    X = np.fft.fft(xw)
    Y = np.fft.fft(yw)

    f = np.arange(N) * (Fs / N)

    # Search positive frequencies excluding DC
    k0 = 1
    k1 = N // 2
    kpk_rel = np.argmax(np.abs(X[k0:k1]))
    kpk = kpk_rel + k0

    f0 = f[kpk]

    ## ===== PHASE DIFFERENCE =====
    phi_x = np.angle(X[kpk])
    phi_y = np.angle(Y[kpk])

    phi = phi_y - phi_x
    phi = np.arctan2(np.sin(phi), np.cos(phi))
    phase_deg = np.degrees(phi)

    ## ===== TIME DELAY in ns =====
    delay_s = -phi / (2 * np.pi * f0)
    delay_ns = delay_s * 1e9

    return f0, phase_deg, delay_ns, X, f, k1


def plot_results(x, y, Fs, f0, phase_deg, delay_ns, X, f, k1, title_prefix=""):
    """Plot time-domain, Lissajous, and spectrum (matches phase_shift.py)."""
    N = len(x)
    t = np.arange(N) / Fs

    fig, axs = plt.subplots(3, 1, num=f"{title_prefix}Phase/Delay Extraction")

    axs[0].plot(t, x, "b", label="x")
    axs[0].plot(t, y, "r", label="y")
    axs[0].grid(True)
    axs[0].set_xlabel("Time (s)")
    axs[0].set_ylabel("Amplitude")
    axs[0].legend()
    axs[0].set_title("Time-domain signals")

    axs[1].plot(x, y, "k")
    axs[1].grid(True)
    axs[1].set_aspect("equal")
    axs[1].set_xlabel("x")
    axs[1].set_ylabel("y")
    axs[1].set_title("X-Y (Lissajous) plot")

    axs[2].plot(f[0:k1], 20 * np.log10(np.abs(X[0:k1]) + np.finfo(float).tiny))
    axs[2].grid(True)
    axs[2].set_xlabel("Frequency (Hz)")
    axs[2].set_ylabel("|X(f)| (dB)")
    axs[2].set_title(f"Spectrum (dominant f0 = {f0:.3g} Hz)")

    plt.tight_layout()


def print_summary(results_before, results_after):
    """Print summary table of all measurements."""
    print("\n" + "=" * 70)
    print("SYNCHRONIZATION STABILITY TEST SUMMARY")
    print("=" * 70)

    print("\n--- BEFORE sync (expect inconsistent phase) ---")
    print(f"{'#':>3}  {'f0 (Hz)':>12}  {'Phase (deg)':>12}  {'Delay (ns)':>12}")
    print("-" * 45)
    for i, (f0, ph, dl) in enumerate(results_before):
        print(f"{i+1:>3}  {f0:>12.1f}  {ph:>12.3f}  {dl:>12.1f}")

    if len(results_before) > 1:
        phases = [r[1] for r in results_before]
        print(f"{'':>3}  {'':>12}  mean={np.mean(phases):>7.3f}  std={np.std(phases):.3f}")

    print("\n--- AFTER sync (expect stable phase) ---")
    print(f"{'#':>3}  {'f0 (Hz)':>12}  {'Phase (deg)':>12}  {'Delay (ns)':>12}")
    print("-" * 45)
    for i, (f0, ph, dl) in enumerate(results_after):
        print(f"{i+1:>3}  {f0:>12.1f}  {ph:>12.3f}  {dl:>12.1f}")

    if len(results_after) > 1:
        phases = [r[1] for r in results_after]
        print(f"{'':>3}  {'':>12}  mean={np.mean(phases):>7.3f}  std={np.std(phases):.3f}")

    print("=" * 70)


def main():
    ## ===== USER SETTINGS =====
    my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    do_pdn = "--no-pdn" not in sys.argv
    ch_a = 0
    ch_b = 4
    buffer_size = 65534
    n_captures = 5

    print("uri: " + str(my_uri))

    dev = adi.ad7134(uri=my_uri)

    dev.rx_enabled_channels = list(range(8))
    dev.rx_buffer_size = buffer_size

    ## ===== SET SAMPLE RATE AND FILTER =====
    dev.sampling_frequency = 1496000
    ODR = float(dev.sampling_frequency)
    Fs = ODR / 2

    print(f"ODR                = {ODR:.6g} Hz")
    print(f"Fs (per channel)   = {Fs:.6g} Hz ({Fs/1e3:.0f} kSPS)")

    ## ===== PDN RESET (break synchronization) =====
    if do_pdn:
        print("\nPDN reset: powering down both AD7134 chips...")
        dev.pdn_reset()
        print("PDN reset complete. Registers reconfigured.")
    else:
        print("\nSkipping PDN reset (--no-pdn).")

    dev.filter_type = "SINC6"
    print(f"Filter type        = {dev.filter_type}")
    print(f"Channels           = x=ch{ch_a} (adc_0), y=ch{ch_b} (adc_1)")
    print(f"Buffer size        = {buffer_size}")
    print(f"Captures per phase = {n_captures}")

    ## ===== CAPTURE WITHOUT SYNC =====
    print("\n--- Capturing WITHOUT sync (sync is broken after PDN) ---")
    results_before = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)

        f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
        results_before.append((f0, phase_deg, delay_ns))

        print(f"  Capture {i+1}: f0={f0:.1f} Hz  phase={phase_deg:.3f} deg  delay={delay_ns:.1f} ns")

    ## ===== SYNC =====
    print("\n--- Calling sync (DIG_IF_RESET broadcast to both chips) ---")
    dev.sync()
    dev.rx()
    dev.rx()
    dev.rx()
    print("Sync complete (3 buffers flushed).")

    ## ===== CAPTURE WITH SYNC =====
    print("\n--- Capturing WITH sync ---")
    results_after = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)

        f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
        results_after.append((f0, phase_deg, delay_ns))

        print(f"  Capture {i+1}: f0={f0:.1f} Hz  phase={phase_deg:.3f} deg  delay={delay_ns:.1f} ns")

    ## ===== SUMMARY =====
    print_summary(results_before, results_after)

    ## ===== DETAILED ANALYSIS (last capture, matches phase_shift.py output) =====
    N = len(x)
    print(f"\n--- Phase/Delay Analysis (last capture, after sync) ---")
    print(f"Fs                 = {Fs:.6g} Hz ({Fs/1e6:.3f} MSPS)")
    print(f"Samples (N)        = {N}")
    print(f"Dominant tone f0   = {f0:.6g} Hz")
    print(f"Phase(ch{ch_b})-Phase(ch{ch_a})  = {phase_deg:.6f} deg")
    print(f"Delay (ch{ch_b} wrt ch{ch_a})    = {delay_ns:.3f} ns  (positive => ch{ch_b} lags ch{ch_a})")

    ## ===== PLOT last capture =====
    plot_results(x, y, Fs, f0, phase_deg, delay_ns, X, f, k1, "After Sync - ")
    plt.show()

    del dev


if __name__ == "__main__":
    main()
