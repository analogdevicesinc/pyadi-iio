# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 phase matching and signal quality test.
# Captures data directly via pyadi-iio (no iio_osc / CSV needed).
#
# Test flow:
#   1. rmmod + modprobe ad4134 for a clean synchronized startup
#   2. Capture N times BEFORE sync (raw boot-time phase offset)
#   3. Sync (DIG_IF_RESET broadcast via cs_gpio)
#   4. Capture N times AFTER sync
#   5. Print before/after summary + signal quality + plot
#
# Convention:
#   phase_deg = phase(y) - phase(x)
#   delay_ns  = -phase_rad / (2*pi*f0) * 1e9
#   delay_ns > 0  => y lags x (y delayed)
#   delay_ns < 0  => y leads x

import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi


def reload_driver(uri):
    """Reload the ad4134 kernel driver for a clean, synchronised startup.

    Uncomment the modprobe block below when ad4134 is built as a loadable
    kernel module (.ko).  With a built-in driver this function is a no-op.
    """
    # ── loadable-module version (rmmod + modprobe) ──────────────────────────
    # modprobe blocks until the full init sequence completes (~12 s):
    # hardware reset → ODR start → simultaneous PDN cycle → PLL lock wait.
    #
    # t0 = time.monotonic()
    # if uri.startswith("ip:"):
    #     host = uri[3:]
    #     print(f"Reloading ad4134 driver on {host} ...")
    #     subprocess.run(
    #         ["ssh", f"root@{host}", "rmmod ad4134 2>/dev/null; modprobe ad4134"],
    #         check=True,
    #     )
    # else:
    #     print("Reloading ad4134 driver locally ...")
    #     subprocess.run(["rmmod", "ad4134"], check=False)
    #     subprocess.run(["modprobe", "ad4134"], check=True)
    # time.sleep(2)  # let iiod enumerate the new IIO devices
    # elapsed = time.monotonic() - t0
    # print(f"Driver reloaded in {elapsed:.1f} s (rmmod + modprobe + iiod settle).")
    # ────────────────────────────────────────────────────────────────────────


def compute_signal_quality(x, Fs, n_harmonics=5):
    """Compute SNR, THD, SINAD, ENOB, SFDR from a single-tone capture."""
    x = x - np.nanmean(x)
    N = len(x)

    w = np.hanning(N)
    xw = x * w

    X = np.fft.fft(xw)
    P = np.abs(X) ** 2

    k_half = N // 2
    f = np.arange(N) * (Fs / N)

    kpk = 1 + np.argmax(P[1:k_half])
    f0 = f[kpk]

    # Fundamental bin range (peak ± 3 bins to capture windowing leakage)
    bw = 3
    k_lo = max(1, kpk - bw)
    k_hi = min(k_half, kpk + bw + 1)
    P_signal = np.sum(P[k_lo:k_hi])

    # Harmonic bins
    P_harmonics = 0.0
    for h in range(2, n_harmonics + 1):
        kh = round(h * kpk)
        if kh >= k_half:
            break
        hlo = max(1, kh - bw)
        hhi = min(k_half, kh + bw + 1)
        P_harmonics += np.sum(P[hlo:hhi])

    # Noise = everything in [1, k_half) minus signal minus harmonics
    P_total = np.sum(P[1:k_half])
    P_noise = P_total - P_signal - P_harmonics

    eps = np.finfo(float).tiny
    snr_db = 10 * np.log10(P_signal / max(P_noise, eps))
    thd_db = 10 * np.log10(max(P_harmonics, eps) / P_signal)
    sinad_db = 10 * np.log10(P_signal / max(P_noise + P_harmonics, eps))
    enob = (sinad_db - 1.76) / 6.02

    # SFDR: fundamental vs. largest single spur (any bin outside fundamental)
    P_scan = P[1:k_half].copy()
    P_scan[k_lo - 1 : k_hi - 1] = 0
    P_spur_peak = np.max(P_scan) if np.any(P_scan > 0) else eps
    sfdr_db = 10 * np.log10(P_signal / max(P_spur_peak, eps))

    # Signal amplitude in dBFS (relative to 24-bit full scale)
    FS_RMS = 8388607 / np.sqrt(2)
    w_cg = np.mean(w)
    signal_rms = np.sqrt(P_signal) / (N * w_cg)
    dbfs = 20 * np.log10(signal_rms / FS_RMS) if signal_rms > 0 else -999

    return {
        "f0": f0,
        "snr_db": snr_db,
        "thd_db": thd_db,
        "sinad_db": sinad_db,
        "enob": enob,
        "sfdr_db": sfdr_db,
        "signal_rms": signal_rms,
        "dbfs": dbfs,
    }


def print_signal_quality(label, sq):
    """Print signal quality metrics."""
    print(f"\n  {label}:")
    print(f"    Fundamental f0 = {sq['f0']:.1f} Hz")
    print(f"    Signal RMS     = {sq['signal_rms']:.0f} codes  ({sq['dbfs']:.1f} dBFS)")
    print(f"    SNR            = {sq['snr_db']:.1f} dB")
    print(f"    THD            = {sq['thd_db']:.1f} dB")
    print(f"    SINAD          = {sq['sinad_db']:.1f} dB")
    print(f"    ENOB           = {sq['enob']:.1f} bits")
    print(f"    SFDR           = {sq['sfdr_db']:.1f} dB")


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

    n_plot = min(N, 2048)
    axs[1].plot(x[:n_plot], y[:n_plot], "k.", markersize=1)
    axs[1].set_aspect("equal")
    axs[1].grid(True)
    axs[1].set_xlabel("x (ch0)")
    axs[1].set_ylabel("y (ch4)")
    axs[1].set_title(f"X-Y (Lissajous) — {phase_deg:.4f} deg, {delay_ns:.1f} ns")

    axs[2].plot(f[0:k1], 20 * np.log10(np.abs(X[0:k1]) + np.finfo(float).tiny))
    axs[2].grid(True)
    axs[2].set_xlabel("Frequency (Hz)")
    axs[2].set_ylabel("|X(f)| (dB)")
    axs[2].set_title(f"Spectrum (dominant f0 = {f0:.3g} Hz)")

    plt.tight_layout()


def print_summary(results):
    """Print summary table of all measurements."""
    print("\n" + "=" * 70)
    print("PHASE MATCHING SUMMARY")
    print("=" * 70)

    print(f"\n{'#':>3}  {'f0 (Hz)':>12}  {'Phase (deg)':>12}  {'Delay (ns)':>12}")
    print("-" * 45)
    for i, (f0, ph, dl) in enumerate(results):
        print(f"{i+1:>3}  {f0:>12.1f}  {ph:>12.3f}  {dl:>12.1f}")

    if len(results) > 1:
        phases = [r[1] for r in results]
        delays = [r[2] for r in results]
        print(f"{'':>3}  {'':>12}  mean={np.mean(phases):>7.3f}  mean={np.mean(delays):>7.1f}")
        print(f"{'':>3}  {'':>12}  std ={np.std(phases):>7.3f}  std ={np.std(delays):>7.1f}")

    print("=" * 70)


def main():
    ## ===== USER SETTINGS =====
    my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    ch_a = 0
    ch_b = 4
    buffer_size = 65534
    n_captures = 5
    n_trials = 10
    target_fs = 1400000

    print("uri: " + str(my_uri))

    all_before = []
    all_after = []
    trial_means = []
    last = {}

    for trial in range(n_trials):
        print(f"\n{'=' * 70}")
        print(f"TRIAL {trial + 1} / {n_trials}")
        print(f"{'=' * 70}")

        reload_driver(my_uri)

        dev = adi.ad7134(uri=my_uri)
        dev.rx_enabled_channels = list(range(8))
        dev.rx_buffer_size = buffer_size
        dev.sampling_frequency = target_fs

        ## ===== READ BACK ACTUAL SAMPLE RATE (PWM-quantised) =====
        Fs = float(dev.sampling_frequency)

        if trial == 0:
            print(f"Fs (target)        = {target_fs} Hz ({target_fs/1e6:.3f} MSPS)")
            print(f"Fs (actual)        = {Fs:.6g} Hz ({Fs/1e6:.3f} MSPS)")
            print(f"Filter type        = {dev.filter_type}")
            print(f"Channels           = x=ch{ch_a} (adc_0), y=ch{ch_b} (adc_1)")
            print(f"Buffer size        = {buffer_size}")
            print(f"Captures/trial     = {n_captures}")
            print(f"Trials             = {n_trials}")

        ## ===== CAPTURE BEFORE SYNC =====
        results_before = []
        for i in range(n_captures):
            data = dev.rx()
            x = np.array(data[ch_a], dtype=np.float64)
            y = np.array(data[ch_b], dtype=np.float64)
            f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
            results_before.append((f0, phase_deg, delay_ns))

        all_before.extend(results_before)

        ## ===== SYNC (DIG_IF_RESET broadcast via cs_gpio) =====
        dev.rx_destroy_buffer()
        dev.sync()
        for _ in range(3):
            dev.rx()

        ## ===== CAPTURE AFTER SYNC =====
        results_after = []
        for i in range(n_captures):
            data = dev.rx()
            x = np.array(data[ch_a], dtype=np.float64)
            y = np.array(data[ch_b], dtype=np.float64)
            f0, phase_deg, delay_ns, X, f, k1 = compute_phase_delay(x, y, Fs)
            results_after.append((f0, phase_deg, delay_ns))

        all_after.extend(results_after)

        before_mean = np.mean([r[2] for r in results_before])
        after_mean = np.mean([r[2] for r in results_after])
        trial_means.append((trial + 1, before_mean, after_mean))
        print(f"\n  Sync effect: {before_mean:.1f} ns → {after_mean:.1f} ns"
              f"  (delta = {after_mean - before_mean:.1f} ns)")

        last = {
            "x": x, "y": y, "Fs": Fs, "f0": f0,
            "phase_deg": phase_deg, "delay_ns": delay_ns,
            "X": X, "f": f, "k1": k1,
        }

        del dev

    ## ===== PER-TRIAL COMPARISON TABLE =====
    print(f"\n\n{'=' * 70}")
    print(f"PER-TRIAL MEAN DELAY COMPARISON")
    print(f"{'=' * 70}")
    print(f"{'Trial':>6}  {'Before sync (ns)':>18}  {'After sync (ns)':>17}  {'Delta (ns)':>12}")
    print("-" * 60)
    for tr, bm, am in trial_means:
        print(f"{tr:>6}  {bm:>18.1f}  {am:>17.1f}  {am - bm:>12.1f}")
    print("-" * 60)
    overall_bm = np.mean([t[1] for t in trial_means])
    overall_am = np.mean([t[2] for t in trial_means])
    print(f"{'mean':>6}  {overall_bm:>18.1f}  {overall_am:>17.1f}  {overall_am - overall_bm:>12.1f}")
    print(f"{'std':>6}  {np.std([t[1] for t in trial_means]):>18.1f}  {np.std([t[2] for t in trial_means]):>17.1f}  {'':>12}")
    print(f"{'=' * 70}")

    ## ===== DETAILED ANALYSIS (last capture of last trial) =====
    x, y = last["x"], last["y"]
    Fs, f0 = last["Fs"], last["f0"]
    phase_deg, delay_ns = last["phase_deg"], last["delay_ns"]
    X, f, k1 = last["X"], last["f"], last["k1"]
    N = len(x)

    print(f"\n--- Phase/Delay Analysis (last capture, trial {n_trials}) ---")
    print(f"Fs                 = {Fs:.6g} Hz ({Fs/1e6:.3f} MSPS)")
    print(f"Samples (N)        = {N}")
    print(f"Dominant tone f0   = {f0:.6g} Hz")
    print(f"Phase(ch{ch_b})-Phase(ch{ch_a})  = {phase_deg:.6f} deg")
    print(f"Delay (ch{ch_b} wrt ch{ch_a})    = {delay_ns:.3f} ns  (positive => ch{ch_b} lags ch{ch_a})")

    ## ===== DATA RANGE CHECK =====
    print(f"\n--- Data Range (last capture) ---")
    x_rms = np.std(x)
    y_rms = np.std(y)
    FS_peak = 8388607
    print(f"  ch{ch_a}: mean={np.mean(x):.0f}  RMS={x_rms:.0f}  min={np.min(x):.0f}  max={np.max(x):.0f}")
    print(f"  ch{ch_b}: mean={np.mean(y):.0f}  RMS={y_rms:.0f}  min={np.min(y):.0f}  max={np.max(y):.0f}")
    n_clip_x = np.sum(np.abs(x) >= FS_peak - 10)
    n_clip_y = np.sum(np.abs(y) >= FS_peak - 10)
    print(f"  Clipped samples: ch{ch_a}={n_clip_x} ({n_clip_x/len(x)*100:.2f}%)"
          f"  ch{ch_b}={n_clip_y} ({n_clip_y/len(y)*100:.2f}%)")

    ## ===== SIGNAL QUALITY (last capture) =====
    print(f"\n--- Signal Quality (last capture) ---")
    sq_x = compute_signal_quality(x, Fs)
    print_signal_quality(f"ch{ch_a} (adc_0)", sq_x)
    sq_y = compute_signal_quality(y, Fs)
    print_signal_quality(f"ch{ch_b} (adc_1)", sq_y)

    ## ===== PLOT (last capture) =====
    plot_results(x, y, Fs, f0, phase_deg, delay_ns, X, f, k1)
    plt.savefig("ad7134_phase_shift.png", dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to ad7134_phase_shift.png")
    plt.show()


if __name__ == "__main__":
    main()
