# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Offline phase / inter-chip-delay analysis of an 8-channel AD7134 iio_osc
# CSV export.  PC-side companion to examples/ad7134_sync_demo.py — same FFT
# phase-delay method as phase_shift.py / phase_shift.m, but reads a saved
# capture instead of talking to the board.
#
# Expected CSV (iio_osc "Save as CSV"): no header, 8 columns, comma-separated
# (a trailing comma per line is tolerated).  Columns map to:
#     0..3 -> adc_0 (chip A) channels 0..3
#     4..7 -> adc_1 (chip B) channels 0..3
#
# Convention (identical to phase_shift.py):
#     phase_deg = phase(y) - phase(x)
#     delay_ns  = -phi / (2*pi*f0) * 1e9
#     delay_ns > 0  => y lags  x (y delayed)
#     delay_ns < 0  => y leads x
#
# IMPORTANT: the ns result scales with Fs, so pass the ACTUAL ODR the capture
# was taken at (e.g. a "1.4 MHz" run is really 1.36986 MHz = 48 MHz / 35).
#
# Usage:
#   python3 ad7134_phase_from_csv.py <csv> [Fs_hz] [ch_ref]
#
# Examples:
#   python3 ad7134_phase_from_csv.py ad7134_odr_rising_edge.csv
#   python3 ad7134_phase_from_csv.py ad7134_odr_rising_edge.csv 1369863
#   python3 ad7134_phase_from_csv.py ad7134_odr_rising_edge.csv 1369863 0

import sys

import matplotlib.pyplot as plt
import numpy as np

# Default sample rate if not given on the command line.
# 1.36986 MHz = 48 MHz / 35, the real rate behind a "1.4 MHz" request.
DEFAULT_FS = 1369863.0

# Skip this many leading rows (iio_osc sometimes emits a 0-filled first sample).
SKIP_ROWS = 0


def compute_phase_delay(x, y, Fs):
    """Return (f0, phase_deg, delay_ns, X, f, k_half) between x and y."""
    x = x - np.nanmean(x)
    y = y - np.nanmean(y)
    N = len(x)
    w = np.hanning(N)
    X = np.fft.fft(x * w)
    Y = np.fft.fft(y * w)
    f = np.arange(N) * (Fs / N)
    # dominant tone: largest positive-frequency bin excluding DC
    kpk = 1 + int(np.argmax(np.abs(X[1 : N // 2])))
    f0 = f[kpk]
    phi = np.angle(Y[kpk]) - np.angle(X[kpk])
    phi = np.arctan2(np.sin(phi), np.cos(phi))  # wrap to [-pi, pi]
    phase_deg = np.degrees(phi)
    delay_ns = -phi / (2 * np.pi * f0) * 1e9
    return f0, phase_deg, delay_ns, X, f, N // 2


def load_csv(path):
    """Load the first 8 columns of a comma-separated iio_osc export."""
    data = np.genfromtxt(path, delimiter=",", usecols=range(8))
    if data.ndim != 2 or data.shape[1] != 8:
        raise ValueError(f"expected 8 columns, got shape {data.shape}")
    # drop rows that are entirely NaN (e.g. a blank trailing line)
    data = data[~np.isnan(data).all(axis=1)]
    if SKIP_ROWS:
        data = data[SKIP_ROWS:]
    return data


def main():
    csv_path = sys.argv[1] if len(sys.argv) >= 2 else "ad7134_odr_rising_edge.csv"
    Fs = float(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_FS
    ch_ref = int(sys.argv[3]) if len(sys.argv) >= 4 else 0

    data = load_csv(csv_path)
    N = data.shape[0]
    t = np.arange(N) / Fs

    print("=" * 64)
    print("AD7134 phase / inter-chip-delay analysis (offline, from CSV)")
    print("=" * 64)
    print(f"File     : {csv_path}")
    print(f"Samples  : {N}")
    print(f"Fs       : {Fs:.6g} Hz ({Fs / 1e6:.4f} MSPS)  [record = {N / Fs * 1e3:.3f} ms]")
    print(f"Reference: ch{ch_ref}  ({'adc_0' if ch_ref < 4 else 'adc_1'})")

    ref = data[:, ch_ref]

    # ── Per-channel delay relative to the reference channel ──────────
    print(f"\n{'-' * 64}")
    print("  Per-channel phase/delay vs reference")
    print(f"{'-' * 64}")
    print(f"  {'ch':>3}  {'chip':>5}   {'f0 (Hz)':>10}   {'phase (deg)':>11}   {'delay (ns)':>10}")
    print(f"  {'-' * 3}  {'-' * 5}   {'-' * 10}   {'-' * 11}   {'-' * 10}")
    delays_vs_ref = []
    f0_ref = 0.0
    for ch in range(8):
        f0, ph, d, *_ = compute_phase_delay(ref, data[:, ch], Fs)
        delays_vs_ref.append(d)
        f0_ref = f0
        chip = "adc_0" if ch < 4 else "adc_1"
        tag = "  <-- ref" if ch == ch_ref else ""
        print(f"  {ch:>3}  {chip:>5}   {f0:>10.1f}   {ph:>+11.3f}   {d:>+10.1f}{tag}")
    delays_vs_ref = np.array(delays_vs_ref)

    # ── Inter-chip pairs: adc_1 chN  vs  adc_0 chN ──────────────────
    print(f"\n{'-' * 64}")
    print("  Inter-chip delay  (adc_1 chN  -  adc_0 chN)")
    print(f"{'-' * 64}")
    print(f"  {'pair':>9}   {'f0 (Hz)':>10}   {'phase (deg)':>11}   {'delay (ns)':>10}")
    print(f"  {'-' * 9}   {'-' * 10}   {'-' * 11}   {'-' * 10}")
    pair_delays = []
    for n in range(4):
        a, b = n, n + 4
        f0, ph, d, *_ = compute_phase_delay(data[:, a], data[:, b], Fs)
        pair_delays.append(d)
        print(f"  ch{b}-ch{a:<5}   {f0:>10.1f}   {ph:>+11.3f}   {d:>+10.1f}")
    pair_delays = np.array(pair_delays)
    print(f"  {'-' * 9}   {'-' * 10}   {'-' * 11}   {'-' * 10}")
    print(f"  {'mean':>9}   {'':>10}   {'':>11}   {pair_delays.mean():>+10.1f}")
    print(f"  {'std':>9}   {'':>10}   {'':>11}   {pair_delays.std():>10.1f}")

    print(f"\n  >> Inter-chip delay (adc_0 -> adc_1): "
          f"{pair_delays.mean():+.1f} ns  (std {pair_delays.std():.1f} ns)")
    print("=" * 64)

    # ── Plot: all 8 channels overlaid + per-channel delay vs ch_ref ──
    # Zoom the time view to ~4 cycles of the dominant tone so the
    # inter-channel shift is actually visible (full record is too dense).
    f0_plot = f0_ref if f0_ref > 0 else Fs / N
    n_plot = min(N, max(256, int(round(Fs / f0_plot * 4))))

    fig, axs = plt.subplots(2, 1, figsize=(11, 9))
    fig.suptitle(f"AD7134 CSV 8-channel phase — ref ch{ch_ref}, "
                 f"f0={f0_plot:.0f} Hz, Fs={Fs / 1e6:.4f} MSPS")

    # Panel 0: all 8 channels overlaid (DC-removed). adc_0 solid, adc_1 dashed.
    for ch in range(8):
        y = data[:, ch] - np.nanmean(data[:, ch])
        chip = "adc_0" if ch < 4 else "adc_1"
        style = "-" if ch < 4 else "--"
        axs[0].plot(t[:n_plot] * 1e3, y[:n_plot], style,
                    label=f"ch{ch} ({chip})", alpha=0.85)
    axs[0].set_xlabel("Time (ms)")
    axs[0].set_ylabel("Amplitude (counts)")
    axs[0].set_title(f"Time-domain (DC-removed, all 8 channels, ~4 cycles)")
    axs[0].legend(ncol=4, fontsize=8)
    axs[0].grid(True)

    # Panel 1: per-channel delay vs ch_ref as horizontal bars (one line/bar
    # per channel) — lets you read the delay spread across all 8 at a glance.
    colors = ["C0"] * 4 + ["C1"] * 4
    ypos = np.arange(8)
    axs[1].barh(ypos, delays_vs_ref, color=colors)
    axs[1].axvline(0, color="k", lw=0.8)
    axs[1].set_yticks(ypos)
    axs[1].set_yticklabels([f"ch{c}" for c in range(8)])
    axs[1].invert_yaxis()  # ch0 at top
    axs[1].set_xlabel(f"delay vs ch{ch_ref} (ns)")
    axs[1].set_title("Per-channel delay relative to reference "
                     "(blue=adc_0, orange=adc_1)")
    axs[1].grid(True, axis="x")
    for c, v in enumerate(delays_vs_ref):
        axs[1].text(v, c, f" {v:+.1f}", va="center",
                    ha="left" if v >= 0 else "right", fontsize=8)

    plt.tight_layout()
    out_png = csv_path.rsplit(".", 1)[0] + "_phase.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved -> {out_png}")
    plt.show()


if __name__ == "__main__":
    main()
