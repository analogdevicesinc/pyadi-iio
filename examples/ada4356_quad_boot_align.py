# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 -- one-shot boot alignment: clock trim + whole-sample shift, no interpolation.

Combines what used to take three scripts on the same boot, same tone on J11:

  1. measure    uncorrected skew of B/C/D vs A        (ada4356_quad_example.py)
  2. clock trim AD9517 fine delay puts each channel's
                sub-sample part on A's, where in reach (ada4356_quad_clock_trim.py --auto)
  3. align      whole-sample shift for every channel, no FIR on any channel
                                                       (ada4356_quad_aligned_example.py ... whole)
  4. verify     re-measure the aligned data, report skew, ENOB, level

A channel the trim cannot fully reach (C, ~+0.5 samp) gets the maximum safe
delay (fraction 36, ~1.8 ns) and keeps the rest of its fraction.

Only the summary is printed.  The clock delays stay applied on exit (the
alignment offsets live in this process only); --restore puts them back in
bypass.  Everything here is valid for this boot only -- re-run after every
power cycle, reboot, gain_mode/filter_mode change or clock sync.

Usage:
  python3 ada4356_quad_boot_align.py ip:192.168.0.102
  python3 ada4356_quad_boot_align.py ip:192.168.0.102 --no-trim     # software only
"""

import argparse
import time

import matplotlib.pyplot as plt
import numpy as np

import adi
from adi.ada4356_quad import CHANNEL_LABELS, _estimate_tone_hz
from ada4356_quad_clock_trim import (
    RAMP,
    SLOPE_NS,
    averaged,
    max_fraction,
    need_samples,
    plan,
)
from ada4356_quad_draw_test import setup

FULL_SCALE = 8192.0
N_HARMONICS = 9


def set_delays(dev, settings):
    for lab, (fr, en) in settings.items():
        dev.set_clock_delay(lab, fr, RAMP, enable=en)


def clock_trim(dev, before, args, fs):
    """Same algorithm as clock_trim.py --auto, without its tables."""
    fmax = max_fraction()
    labs = "BCD"
    # Enabling the delay path alone shifts a channel by 0.24-0.41 ns (measured).
    set_delays(dev, {lab: (0, True) for lab in labs})
    time.sleep(args.settle)
    mid, _ = averaged(dev, args.tone, args.captures)

    settings = {}
    for j, lab in enumerate(labs):
        st = plan(need_samples(before[j]), mid[j] - before[j], SLOPE_NS, fs, fmax)
        # Out of reach (C): the maximum safe delay still takes ~1.8 ns off its fraction.
        settings[lab] = st or (fmax, True)
    set_delays(dev, settings)
    time.sleep(args.settle)
    after, _ = averaged(dev, args.tone, args.captures)

    # One refinement with each channel's own measured slope.
    refined = {}
    for j, lab in enumerate(labs):
        fr, en = settings[lab]
        moved = after[j] - mid[j]
        if not en or not fr or not 0 < moved < 0.5:
            continue
        slope = moved / fs * 1e9 / fr
        st = plan(need_samples(before[j]), mid[j] - before[j], slope, fs, fmax)
        if st and st != (fr, en):
            refined[lab] = st
    if refined:
        set_delays(dev, refined)
        settings.update(refined)
        time.sleep(args.settle)
    return settings


def align(dev, tone):
    """Whole-sample shift on every channel; the data values are not touched."""
    cal = dev.calibrate_alignment(tone, verbose=False, subsample=False)
    return [cal["removed_samples"][c] for c in CHANNEL_LABELS]


def quality(x, f0, fs):
    """Amplitude, DC, ENOB and the full SNR/THD/SFDR/SINAD set (as in ada4356_quad_example.py)."""
    n = np.arange(x.size)
    cols = [np.ones(x.size)]
    for h in range(1, N_HARMONICS + 1):
        if h * f0 >= fs / 2:
            break
        w = 2 * np.pi * f0 * h * n / fs
        cols += [np.cos(w), np.sin(w)]
    m = np.column_stack(cols)
    coef = np.linalg.solve(m.T @ m, m.T @ x)
    resid = x - m @ coef
    amps = np.hypot(coef[1::2], coef[2::2])
    a1, harm = amps[0], amps[1:]
    noise_rms = np.std(resid)

    # Largest non-harmonic spur, from the windowed spectrum of the residual.
    window = np.hanning(x.size)
    rspec = np.abs(np.fft.rfft(resid * window)) * 4.0 / x.size
    rspec[:10] = 0.0
    for h in range(1, N_HARMONICS + 1):
        b = int(round(f0 * h * x.size / fs))
        if b < len(rspec):
            rspec[max(0, b - 5): b + 6] = 0.0
    spur = rspec.max()
    spur_hz = np.fft.rfftfreq(x.size, 1.0 / fs)[int(np.argmax(rspec))]

    worst = max(spur, harm.max() if harm.size else 0.0)
    sfdr = 20 * np.log10(a1 / worst) if worst > 0 else np.inf
    thd = 10 * np.log10(np.sum(harm**2) / a1**2) if harm.size else -np.inf
    snr_fs = 20 * np.log10((FULL_SCALE / np.sqrt(2)) / noise_rms)
    sinad = 10 * np.log10((a1**2 / 2) / (noise_rms**2 + np.sum(harm**2) / 2))
    sinad_fs = sinad + 20 * np.log10(FULL_SCALE / a1)
    enob = (sinad_fs - 1.76) / 6.02
    return a1, coef[0], enob, resid, noise_rms, snr_fs, thd, sfdr, sinad_fs, spur, spur_hz


MAX_LAG = 64


def autocorrelation(r, max_lag=MAX_LAG):
    """Normalised residual autocorrelation via Wiener-Khinchin (O(N log N))."""
    r = r - r.mean()
    nfft = 1 << int(np.ceil(np.log2(2 * r.size)))
    s = np.fft.rfft(r, nfft)
    ac = np.fft.irfft(np.abs(s) ** 2, nfft)[: max_lag + 1]
    return ac / ac[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.102")
    ap.add_argument("--tone", type=float, default=100e3)
    ap.add_argument("--samples", type=int, default=65536)
    ap.add_argument("--gain", default="11k")
    ap.add_argument("--filter", default="fsel1")
    ap.add_argument("--captures", type=int, default=5, help="averaged per measurement")
    ap.add_argument("--settle", type=float, default=1.0)
    ap.add_argument("--target-ns", type=float, default=0.3)
    ap.add_argument("--no-trim", action="store_true", help="skip the AD9517 trim")
    ap.add_argument("--restore", action="store_true", help="put the clock delays back in bypass on exit")
    args = ap.parse_args()

    dev = adi.ada4356_quad(uri=args.uri)
    setup(dev, args)
    fs = dev.sampling_frequency
    ns = 1e9 / fs

    trim = {}
    try:
        if not args.no_trim:
            # A second run in the same boot would otherwise plan on top of the kept delays.
            dev.bypass_clock_delays()
            time.sleep(args.settle)
        print("measuring uncorrected skew ...")
        before, _ = averaged(dev, args.tone, args.captures)
        print("  " + "  ".join(f"{lab}{b * ns:+.2f}ns" for lab, b in zip("BCD", before)))
        if not args.no_trim:
            print("trimming AD9517 clocks ...")
            trim = clock_trim(dev, before, args, fs)
            print("  " + "  ".join(
                f"{lab}:{('-' if not en else (str(fr) + (' max' if fr == max_fraction() else '')))}"
                for lab, (fr, en) in trim.items()))
        print("calibrating alignment ...")
        offsets = align(dev, args.tone)
        print("  " + "  ".join(f"{lab}{o:+d}samp" for lab, o in zip(CHANNEL_LABELS, offsets)))
        print("verifying ...")
        after, _ = averaged(dev, args.tone, args.captures)
        print("  " + "  ".join(f"{lab}{a * ns:+.2f}ns" for lab, a in zip("BCD", after)))
        data = [np.asarray(x, dtype=np.float64) for x in dev.rx()]
    except BaseException:
        if trim:
            dev.bypass_clock_delays()
            print("  aborted: clock delays restored to bypass")
        raise

    f0 = _estimate_tone_hz(data[0], args.tone, fs)
    q = [quality(x, f0, fs) for x in data]
    before = np.concatenate(([0.0], before))
    after = np.concatenate(([0.0], after))

    print(f"\n=== Boot alignment  ({f0 / 1e3:.3f} kHz, {args.gain}/{args.filter}, "
          f"{args.captures} captures/measurement) ===")
    fmax = max_fraction()
    print(f"  Ch  {'before':>8}  {'clock trim':>10}  {'shift':>7}  {'after':>8}  "
          f"{'ENOB':>6}  {'dBFS':>7}  {'pedestal':>9}")
    print(f"      {'(ns)':>8}  {'(fraction)':>10}  {'(samp)':>7}  {'(ns)':>8}")
    for i, lab in enumerate(CHANNEL_LABELS):
        fr, en = trim.get(lab, (0, False))
        t = "-" if lab == "A" else (f"{fr}" + (" max" if fr == fmax else "") if en else "bypass")
        a1, dc, enob = q[i][0], q[i][1], q[i][2]
        print(f"  {lab}  {before[i] * ns:>8.2f}  {t:>10}  {offsets[i]:>+7d}  "
              f"{after[i] * ns:>8.2f}  {enob:>6.2f}  "
              f"{20 * np.log10(a1 / FULL_SCALE):>7.2f}  {dc:>9.0f}")

    print(f"\n  spread before: {np.ptp(before) * ns:.2f} ns   after: {np.ptp(after) * ns:.2f} ns")
    off = [lab for lab, a in zip(CHANNEL_LABELS, after) if abs(a) * ns >= args.target_ns]
    if off:
        print(f"  above target: {', '.join(off)} -- fraction beyond the clock trim's range "
              "(max delay applied), rest left in (no interpolation)")
    flip = [lab for lab, a in zip(CHANNEL_LABELS, after) if abs(a) > 0.4]
    if flip:
        print(f"  near half a sample: {', '.join(flip)} -- the whole shift can differ by 1 "
              "between runs (+-4 ns)")

    clipped = [lab for lab, x in zip(CHANNEL_LABELS, data)
               if x.max() >= FULL_SCALE - 1 or x.min() <= -FULL_SCALE + 1]
    if clipped:
        print(f"  *** CLIPPING on {', '.join(clipped)}: every number above is invalid")

    if args.restore:
        dev.bypass_clock_delays()
        print("  clock delays restored to bypass")
    elif trim:
        print("  clock delays left applied (a reboot restores bypass)")
    print("  valid for this boot only; the shift lives in this process (rx() of this object)")

    print(f"\n=== Signal quality (harmonics 2..{N_HARMONICS} removed) ===")
    print(f"  Ch  {'ampl':>8}  {'dBFS':>7}  {'noise':>7}  {'SNR/FS':>7}  "
          f"{'THD':>8}  {'SFDR':>7}  {'SINAD':>7}  worst spur")
    for lab, (a1, dc, enob, _, noise_rms, snr_fs, thd, sfdr, sinad_fs, spur, spur_hz) in zip(CHANNEL_LABELS, q):
        print(f"  {lab}  {a1:>8.1f}  {20 * np.log10(a1 / FULL_SCALE):>7.2f}  {noise_rms:>7.2f}  "
              f"{snr_fs:>7.2f}  {thd:>8.2f}  {sfdr:>7.2f}  {sinad_fs:>7.2f}  "
              f"{20 * np.log10(spur / a1):>6.1f} dBc @ {spur_hz / 1e6:.3f} MHz")
    print("  ampl/noise in ADC codes; dB values in dB")

    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
    zoom_n = min(int(fs / f0 * 5), data[0].size)
    t_us = np.arange(zoom_n) / fs * 1e6
    window = np.hanning(data[0].size)
    freq_mhz = np.fft.rfftfreq(data[0].size, d=1.0 / fs) / 1e6

    fig = plt.figure(figsize=(15, 11))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.1, 1, 1], hspace=0.38, wspace=0.18)

    ax_t = fig.add_subplot(gs[0, :])
    for x, lab, color in zip(data, CHANNEL_LABELS, colors):
        ax_t.plot(t_us, (x - x.mean())[:zoom_n], label=f"Ch {lab}", color=color, linewidth=0.8)
    ax_t.set_xlabel("Time (µs)")
    ax_t.set_ylabel("ADC codes (DC removed)")
    ax_t.set_title(f"Boot-aligned capture — {f0 / 1e3:.3f} kHz — 5 periods")
    ax_t.legend(loc="upper right", ncol=4)
    ax_t.grid(True, alpha=0.3)

    for idx, (x, lab, color) in enumerate(zip(data, CHANNEL_LABELS, colors)):
        ax = fig.add_subplot(gs[1 + idx // 2, idx % 2])
        s = np.fft.rfft(x * window)
        psd = 20 * np.log10(np.abs(s) * 4 / data[0].size / FULL_SCALE + 1e-20)
        ax.plot(freq_mhz, psd, color=color, linewidth=0.6)
        a1, dc, enob, _, _, _, _, _, _, _, _ = q[idx]
        ax.set_title(f"Ch {lab} — {20 * np.log10(a1 / FULL_SCALE):.1f} dBFS, "
                     f"ENOB {enob:.2f}, skew {after[idx] * ns:+.2f} ns", fontsize=10)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("dBFS")
        ax.set_ylim(-180, 5)
        ax.grid(True, alpha=0.3)

    plt.savefig("/tmp/ada4356_boot_align.png", dpi=150, bbox_inches="tight")
    print("\nPlot saved: /tmp/ada4356_boot_align.png")

    # --- Second figure: residual autocorrelation (is the leftover noise white?) --
    sig_bound = 3.0 / np.sqrt(data[0].size)
    acfs = [autocorrelation(q[idx][3]) for idx in range(len(data))]

    fig2, ax2 = plt.subplots(figsize=(11, 6.5))
    zc_best, dom_best, best_corr = None, None, -1.0
    for idx, (acf, lab, color) in enumerate(zip(acfs, CHANNEL_LABELS, colors)):
        ax2.plot(np.arange(1, MAX_LAG + 1), acf[1:], color=color, linewidth=1.0,
                 marker=".", markersize=3, label=f"Ch {lab} — $r_1$={acf[1]:.3f}")
        neg = np.flatnonzero(acf[1:] < 0)
        if neg.size:
            z = neg[0] + 1
            zc = z - 1 + acf[z - 1] / (acf[z - 1] - acf[z])
            if acf[1] > best_corr:
                best_corr, zc_best, dom_best = acf[1], zc, fs / (4 * zc)

    ax2.axhspan(-sig_bound, sig_bound, color="gray", alpha=0.35,
                label=f"white noise would live entirely inside this (±{sig_bound:.4f})")
    for lag in (4, 8, 16, 32):
        ax2.axvline(lag, color="gray", linestyle=":", linewidth=0.6)
    ax2.annotate("lags 4/8/16/32 = clock-divider and SERDES-word\n"
                 "fault signatures; smooth here means the digital side is clean",
                 xy=(0.015, 0.03), xycoords="axes fraction", fontsize=8, color="gray")
    if zc_best is not None:
        ax2.axvline(zc_best, color="k", linestyle="--", linewidth=0.9)
        ax2.axhline(0.0, color="k", linewidth=0.5)
        ax2.annotate(f"zero crossing at lag {zc_best:.1f}\n= quarter period\n"
                     f"$\\rightarrow$ {dom_best / 1e6:.2f} MHz",
                     xy=(zc_best, 0.0), xytext=(zc_best + 0.08 * MAX_LAG, 0.45),
                     fontsize=9,
                     arrowprops=dict(arrowstyle="->", color="k", linewidth=0.8),
                     bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.75))
        headline = (f"Residual autocorrelation — the leftover is a {dom_best / 1e6:.2f} MHz "
                    "tone, not noise")
    else:
        headline = "Residual autocorrelation — leftover is white, the noise column is real"

    ax2.set_xlabel("Lag (samples)")
    ax2.set_ylabel("Normalised autocorrelation")
    ax2.set_title(headline)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, alpha=0.3)

    plt.savefig("/tmp/ada4356_boot_align_diag.png", dpi=150, bbox_inches="tight")
    print("Plot saved: /tmp/ada4356_boot_align_diag.png")


if __name__ == "__main__":
    main()
