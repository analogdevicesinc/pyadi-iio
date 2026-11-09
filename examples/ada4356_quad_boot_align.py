# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 boot alignment: measure, AD9517 clock trim, whole-sample shift.

Needs the same tone on all four inputs (J11).  Stages:

  1. measure     skew of B/C/D vs A, with the clock delays in bypass
  2. clock trim  AD9517 fine delay moves each channel's sub-sample skew onto A's;
                 a channel out of reach (usually C) gets the maximum safe delay
  3. align       whole-sample software shift, no interpolation
  4. verify      re-measure; print skew, signal quality and two plots

Clock delays stay applied on exit (--restore bypasses them); the shift lives in
this process only.  Re-run after every power cycle, gain/filter change or clock
sync.

Usage:
  python3 ada4356_quad_boot_align.py ip:192.168.0.102
  python3 ada4356_quad_boot_align.py ip:192.168.0.102 --no-trim     # software only
  python3 ada4356_quad_boot_align.py ip:192.168.0.102 --no-align    # clock trim only
  python3 ada4356_quad_boot_align.py ip:192.168.0.102 --no-trim --no-align  # measure only
"""

import argparse
import time

import matplotlib.pyplot as plt
import numpy as np

import adi
from adi.ada4356_quad import (
    AD9517_DELAY_SAFE_PS,
    CHANNEL_LABELS,
    _estimate_tone_hz,
    ad9517_delay_estimate_ps,
)

TDD_CLOCK_HZ = 125_000_000
FULL_SCALE = 8192.0
N_HARMONICS = 9
RAMP = 0x39
# ns per fraction LSB at ramp 0x39, measured on A and D.
SLOPE_NS = 0.040


def setup(dev, args):
    # Gain and filter move the group delay: set them first.
    dev.gain_mode = args.gain
    dev.filter_mode = args.filter
    dev.rx_buffer_size = args.samples
    tdd = dev.tdd
    tdd.enable = False
    tdd.burst_count = 0
    tdd.frame_length_raw = TDD_CLOCK_HZ
    tdd.channel[0].enable = False
    for ch_idx in range(1, 5):
        tdd.channel[ch_idx].on_raw = 100
        tdd.channel[ch_idx].off_raw = 200
        tdd.channel[ch_idx].enable = True
    tdd.enable = True
    try:
        tdd.sync_soft = True
    except Exception:
        pass
    time.sleep(0.3)


def sine_fit(x, f0, fs):
    """DC and phase of x at f0, fitted jointly (a plain mean biases both)."""
    w = 2 * np.pi * f0 / fs * np.arange(x.size)
    m = np.column_stack([np.ones_like(w), np.cos(w), np.sin(w)])
    dc, a, b = np.linalg.lstsq(m, x, rcond=None)[0]
    return dc, np.arctan2(-b, a)


def measure(dev, tone):
    """Skew of B/C/D vs A in samples, from one capture."""
    data = [np.asarray(x, dtype=np.float64) for x in dev.rx()]
    fs = dev.sampling_frequency
    f0 = _estimate_tone_hz(data[0], tone, fs)
    ph = [sine_fit(x, f0, fs)[1] for x in data]
    # Negative = channel lags A.
    return [
        ((p - ph[0] + np.pi) % (2 * np.pi) - np.pi) / (2 * np.pi) * fs / f0
        for p in ph[1:]
    ]


def averaged(dev, tone, n):
    rows = np.array([measure(dev, tone) for _ in range(n)])
    return rows.mean(axis=0), rows.std(axis=0)


def max_fraction():
    f = 0
    while f < 47 and ad9517_delay_estimate_ps(RAMP, f + 1) <= AD9517_DELAY_SAFE_PS:
        f += 1
    return f


def need_samples(s):
    """Samples to add to put s on a whole sample (delay only adds; skew goes up)."""
    return (np.round(s) - s) % 1.0


def plan(need, insertion, slope_ns, fs, fmax):
    """(fraction, enable) closest to need, given the enable step and the slope."""
    rest_ns = (need - insertion) / fs * 1e9
    if rest_ns < 0:
        # Enabling alone overshoots: pick the closer of bypass and fraction 0.
        return (0, bool(insertion - need < need))
    frac = int(round(rest_ns / slope_ns))
    return (frac, True) if frac <= fmax else None


def set_delays(dev, settings):
    for lab, (fr, en) in settings.items():
        dev.set_clock_delay(lab, fr, RAMP, enable=en)


def trim_label(fr, en, fmax, off="bypass"):
    """Fraction, with ' max' when it sits on the safety cap, or `off` when bypassed."""
    if not en:
        return off
    return f"{fr}" + (" max" if fr == fmax else "")


def clock_trim(dev, before, args, fs):
    """Put each channel's sub-sample skew on A's with the AD9517 fine delay."""
    fmax = max_fraction()
    labs = "BCD"
    # The delay path alone adds 0.24-0.41 ns (measured).
    set_delays(dev, {lab: (0, True) for lab in labs})
    time.sleep(args.settle)
    mid, _ = averaged(dev, args.tone, args.captures)

    settings = {}
    for j, lab in enumerate(labs):
        st = plan(need_samples(before[j]), mid[j] - before[j], SLOPE_NS, fs, fmax)
        # Out of reach: take the maximum safe delay.
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
    """Fit x at f0: amplitude, DC, ENOB, residual, noise, SNR/THD/SFDR/SINAD, spur."""
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
            rspec[max(0, b - 5) : b + 6] = 0.0
    spur = rspec.max()
    spur_hz = np.fft.rfftfreq(x.size, 1.0 / fs)[int(np.argmax(rspec))]

    worst = max(spur, harm.max() if harm.size else 0.0)
    sfdr = 20 * np.log10(a1 / worst) if worst > 0 else np.inf
    thd = 10 * np.log10(np.sum(harm ** 2) / a1 ** 2) if harm.size else -np.inf
    snr_fs = 20 * np.log10((FULL_SCALE / np.sqrt(2)) / noise_rms)
    sinad = 10 * np.log10((a1 ** 2 / 2) / (noise_rms ** 2 + np.sum(harm ** 2) / 2))
    sinad_fs = sinad + 20 * np.log10(FULL_SCALE / a1)
    enob = (sinad_fs - 1.76) / 6.02
    return (
        a1,
        coef[0],
        enob,
        resid,
        noise_rms,
        snr_fs,
        thd,
        sfdr,
        sinad_fs,
        spur,
        spur_hz,
    )


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
    ap.add_argument(
        "--no-align", action="store_true", help="skip the whole-sample software shift"
    )
    ap.add_argument(
        "--restore",
        action="store_true",
        help="put the clock delays back in bypass on exit",
    )
    args = ap.parse_args()

    dev = adi.ada4356_quad(uri=args.uri)
    setup(dev, args)
    fs = dev.sampling_frequency
    ns = 1e9 / fs
    fmax = max_fraction()

    trim = {}
    try:
        # Start from the raw skew; a previous run may have left delays applied.
        dev.bypass_clock_delays()
        time.sleep(args.settle)
        print("measuring uncorrected skew ...")
        before, _ = averaged(dev, args.tone, args.captures)
        print(
            "  " + "  ".join(f"{lab}{b * ns:+.2f}ns" for lab, b in zip("BCD", before))
        )
        if not args.no_trim:
            print("trimming AD9517 clocks ...")
            trim = clock_trim(dev, before, args, fs)
            print(
                "  "
                + "  ".join(
                    f"{lab}:{trim_label(fr, en, fmax, off='-')}"
                    for lab, (fr, en) in trim.items()
                )
            )
        if args.no_align:
            offsets = [0] * len(CHANNEL_LABELS)
        else:
            print("calibrating alignment ...")
            offsets = align(dev, args.tone)
            print(
                "  "
                + "  ".join(
                    f"{lab}{o:+d}samp" for lab, o in zip(CHANNEL_LABELS, offsets)
                )
            )
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

    print(
        f"\n=== Boot alignment  ({f0 / 1e3:.3f} kHz, {args.gain}/{args.filter}, "
        f"{args.captures} captures/measurement) ==="
    )
    print(
        f"  Ch  {'before':>8}  {'clock trim':>10}  {'shift':>7}  {'after':>8}  "
        f"{'ENOB':>6}  {'dBFS':>7}  {'pedestal':>9}"
    )
    print(f"      {'(ns)':>8}  {'(fraction)':>10}  {'(samp)':>7}  {'(ns)':>8}")
    for i, lab in enumerate(CHANNEL_LABELS):
        fr, en = trim.get(lab, (0, False))
        t = "-" if lab == "A" else trim_label(fr, en, fmax)
        a1, dc, enob = q[i][0], q[i][1], q[i][2]
        print(
            f"  {lab}  {before[i] * ns:>8.2f}  {t:>10}  {offsets[i]:>+7d}  "
            f"{after[i] * ns:>8.2f}  {enob:>6.2f}  "
            f"{20 * np.log10(a1 / FULL_SCALE):>7.2f}  {dc:>9.0f}"
        )

    print(
        f"\n  spread before: {np.ptp(before) * ns:.2f} ns   after: {np.ptp(after) * ns:.2f} ns"
    )
    # Without the shift, "after" keeps the whole-sample draw: no target.
    if not args.no_align:
        off = [
            lab
            for lab, a in zip(CHANNEL_LABELS, after)
            if abs(a) * ns >= args.target_ns
        ]
        if off:
            if args.no_trim:
                why = "clock trim skipped, sub-sample fraction left in"
            else:
                why = "fraction beyond the clock trim's range (max delay applied), rest left in"
            print(f"  above target: {', '.join(off)} -- {why} (no interpolation)")
        flip = [lab for lab, a in zip(CHANNEL_LABELS, after) if abs(a) > 0.4]
        if flip:
            print(
                f"  near half a sample: {', '.join(flip)} -- the whole shift can differ "
                "by 1 between runs (+-4 ns)"
            )

    clipped = [
        lab
        for lab, x in zip(CHANNEL_LABELS, data)
        if x.max() >= FULL_SCALE - 1 or x.min() <= -FULL_SCALE + 1
    ]
    if clipped:
        print(f"  *** CLIPPING on {', '.join(clipped)}: every number above is invalid")

    if args.restore:
        dev.bypass_clock_delays()
        print("  clock delays restored to bypass")
    elif trim:
        print("  clock delays left applied (a reboot restores bypass)")
    if not args.no_align:
        print(
            "  valid for this boot only; the shift lives in this process "
            "(rx() of this object)"
        )

    print(f"\n=== Signal quality (harmonics 2..{N_HARMONICS} removed) ===")
    print(
        f"  Ch  {'ampl':>8}  {'dBFS':>7}  {'noise':>7}  {'SNR/FS':>7}  "
        f"{'THD':>8}  {'SFDR':>7}  {'SINAD':>7}  worst spur"
    )
    for (
        lab,
        (a1, dc, enob, _, noise_rms, snr_fs, thd, sfdr, sinad_fs, spur, spur_hz),
    ) in zip(CHANNEL_LABELS, q):
        print(
            f"  {lab}  {a1:>8.1f}  {20 * np.log10(a1 / FULL_SCALE):>7.2f}  {noise_rms:>7.2f}  "
            f"{snr_fs:>7.2f}  {thd:>8.2f}  {sfdr:>7.2f}  {sinad_fs:>7.2f}  "
            f"{20 * np.log10(spur / a1):>6.1f} dBc @ {spur_hz / 1e6:.3f} MHz"
        )
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
        ax_t.plot(
            t_us, (x - x.mean())[:zoom_n], label=f"Ch {lab}", color=color, linewidth=0.8
        )
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
        ax.set_title(
            f"Ch {lab} — {20 * np.log10(a1 / FULL_SCALE):.1f} dBFS, "
            f"ENOB {enob:.2f}, skew {after[idx] * ns:+.2f} ns",
            fontsize=10,
        )
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("dBFS")
        ax.set_ylim(-180, 5)
        ax.grid(True, alpha=0.3)

    plt.savefig("/tmp/ada4356_boot_align.png", dpi=150, bbox_inches="tight")
    print("\nPlot saved: /tmp/ada4356_boot_align.png")

    # Residual autocorrelation: is the leftover noise white?
    sig_bound = 3.0 / np.sqrt(data[0].size)
    acfs = [autocorrelation(q[idx][3]) for idx in range(len(data))]

    fig2, ax2 = plt.subplots(figsize=(11, 6.5))
    zc_best, dom_best, best_corr = None, None, -1.0
    for idx, (acf, lab, color) in enumerate(zip(acfs, CHANNEL_LABELS, colors)):
        ax2.plot(
            np.arange(1, MAX_LAG + 1),
            acf[1:],
            color=color,
            linewidth=1.0,
            marker=".",
            markersize=3,
            label=f"Ch {lab} — $r_1$={acf[1]:.3f}",
        )
        neg = np.flatnonzero(acf[1:] < 0)
        if neg.size:
            z = neg[0] + 1
            zc = z - 1 + acf[z - 1] / (acf[z - 1] - acf[z])
            if acf[1] > best_corr:
                best_corr, zc_best, dom_best = acf[1], zc, fs / (4 * zc)

    ax2.axhspan(
        -sig_bound,
        sig_bound,
        color="gray",
        alpha=0.35,
        label=f"white noise would live entirely inside this (±{sig_bound:.4f})",
    )
    for lag in (4, 8, 16, 32):
        ax2.axvline(lag, color="gray", linestyle=":", linewidth=0.6)
    ax2.annotate(
        "lags 4/8/16/32 = clock-divider and SERDES-word\n"
        "fault signatures; smooth here means the digital side is clean",
        xy=(0.015, 0.03),
        xycoords="axes fraction",
        fontsize=8,
        color="gray",
    )
    if zc_best is not None:
        ax2.axvline(zc_best, color="k", linestyle="--", linewidth=0.9)
        ax2.axhline(0.0, color="k", linewidth=0.5)
        ax2.annotate(
            f"zero crossing at lag {zc_best:.1f}\n= quarter period\n"
            f"$\\rightarrow$ {dom_best / 1e6:.2f} MHz",
            xy=(zc_best, 0.0),
            xytext=(zc_best + 0.08 * MAX_LAG, 0.45),
            fontsize=9,
            arrowprops=dict(arrowstyle="->", color="k", linewidth=0.8),
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.75),
        )
        headline = (
            f"Residual autocorrelation — the leftover is a {dom_best / 1e6:.2f} MHz "
            "tone, not noise"
        )
    else:
        headline = (
            "Residual autocorrelation — leftover is white, the noise column is real"
        )

    ax2.set_xlabel("Lag (samples)")
    ax2.set_ylabel("Normalised autocorrelation")
    ax2.set_title(headline)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, alpha=0.3)

    plt.savefig("/tmp/ada4356_boot_align_diag.png", dpi=150, bbox_inches="tight")
    print("Plot saved: /tmp/ada4356_boot_align_diag.png")


if __name__ == "__main__":
    main()
