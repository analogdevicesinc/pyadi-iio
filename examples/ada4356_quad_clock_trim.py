# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 -- shift the AD9517 ADC clocks and measure the effect on sync.

Same boot, same tone on J11: measure the B/C/D skew vs A, apply AD9517 fine
delays (and optionally a divider phase), measure again, print before/after.
Uncorrected data throughout (no calibrate_alignment()).

  --delay B=20,D=6   apply these fine-delay fractions (ramp 0x39)
  --auto             enable each channel's delay path at fraction 0 to measure
                     its insertion offset (~0.4-0.5 ns), then size the fraction
                     that puts its sub-sample part on A's; refine once
  --phase CD=1       divider phase offset (4 ns/step, shared by the pair) + sync;
                     restarts all four ADC clocks

Settings go back to bypass / phase 0 on exit unless --keep.  A is left alone
unless --allow-a: both board freezes so far happened with a delay on A's clock
or during a sweep.

Usage:
  python3 ada4356_quad_clock_trim.py ip:192.168.0.102 --delay D=20
  python3 ada4356_quad_clock_trim.py ip:192.168.0.102 --auto --keep
"""

import argparse
import time

import numpy as np

import adi
from adi.ada4356_quad import AD9517_DELAY_SAFE_PS, CHANNEL_LABELS, ad9517_delay_estimate_ps
from ada4356_quad_draw_test import measure, setup

RAMP = 0x39
SLOPE_NS = 0.040  # measured 2026-10-19 on A and D at ramp 0x39; the 0.060 estimate is high


def parse_pairs(text):
    out = {}
    for item in filter(None, (text or "").split(",")):
        key, val = item.split("=")
        out[key.strip().upper()] = int(val, 0)
    return out


def max_fraction():
    f = 0
    while f < 47 and ad9517_delay_estimate_ps(RAMP, f + 1) <= AD9517_DELAY_SAFE_PS:
        f += 1
    return f


def averaged(dev, tone, n):
    rows = np.array([measure(dev, tone)[0] for _ in range(n)])
    return rows.mean(axis=0), rows.std(axis=0)


def report(title, skew, sd, fs):
    full = np.concatenate(([0.0], skew))
    frac = full - np.round(full)
    print(f"\n=== {title} ===")
    print("  Ch    skew (samp)    sd      skew (ns)   whole   frac (samp)")
    for lab, s, d, f in zip(CHANNEL_LABELS, full, np.concatenate(([0.0], sd)), frac):
        print(f"  {lab}   {s:+11.4f}  {d:7.4f}  {s / fs * 1e9:+10.2f}   {int(round(s)):+4d}   {f:+8.4f}")
    print(f"  spread, total     : {np.ptp(full):.4f} samp = {np.ptp(full) / fs * 1e9:.2f} ns")
    print(f"  spread, fractions : {np.ptp(frac):.4f} samp = {np.ptp(frac) / fs * 1e9:.2f} ns")


def need_samples(s):
    """Samples to add to put s on a whole sample (delay only adds; skew goes up)."""
    return (np.round(s) - s) % 1.0


def plan(need, insertion, slope_ns, fs, fmax):
    """(fraction, enable) closest to need, given the enable step and the slope."""
    rest_ns = (need - insertion) / fs * 1e9
    if rest_ns < 0:
        # Enabling alone overshoots: keep whichever of bypass / enabled-at-0 lands closer.
        return (0, bool(insertion - need < need))
    frac = int(round(rest_ns / slope_ns))
    return (frac, True) if frac <= fmax else None


def apply_delays(dev, settings):
    for lab, st in settings.items():
        if st is None:
            continue
        fr, en = st
        dev.set_clock_delay(lab, fr, RAMP, enable=en)
        what = f"fraction {fr}" if en else "bypassed"
        print(f"  OUT{4 + CHANNEL_LABELS.index(lab)} ({lab}) fine delay {what}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.102")
    ap.add_argument("--delay", default="", help="e.g. B=20,D=6")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--phase", default="", help="e.g. CD=1 (4 ns/step, applies with a sync)")
    ap.add_argument("--allow-a", action="store_true")
    ap.add_argument("--keep", action="store_true", help="leave the settings applied on exit")
    ap.add_argument("--captures", type=int, default=5)
    ap.add_argument("--tone", type=float, default=100e3)
    ap.add_argument("--samples", type=int, default=65536)
    ap.add_argument("--gain", default="11k")
    ap.add_argument("--filter", default="fsel1")
    ap.add_argument("--settle", type=float, default=1.0)
    args = ap.parse_args()

    delays = {k: (v, v > 0) for k, v in parse_pairs(args.delay).items()}
    phases = parse_pairs(args.phase)
    allowed = set("ABCD" if args.allow_a else "BCD")
    for lab in delays:
        if lab not in allowed:
            raise SystemExit(f"--delay {lab}: not allowed (A needs --allow-a)")

    dev = adi.ada4356_quad(uri=args.uri)
    setup(dev, args)
    fs = dev.sampling_frequency
    fmax = max_fraction()
    touched = set()

    try:
        before, sd = averaged(dev, args.tone, args.captures)
        report("before (all delays bypassed)", before, sd, fs)
        before0 = before

        if phases:
            for pair, n in phases.items():
                print(f"  divider phase {pair} = {n} ({4 * n} ns), sync: all ADC clocks restart")
                dev.set_clock_phase(pair, n)
            time.sleep(args.settle)
            before, sd = averaged(dev, args.tone, args.captures)
            report("after phase (delays still bypassed)", before, sd, fs)

        if args.auto:
            labs = [c for c in "BCD" if c in allowed]
            apply_delays(dev, {c: (0, True) for c in labs})
            touched |= set(labs)
            time.sleep(args.settle)
            mid, sd = averaged(dev, args.tone, args.captures)
            report("delay path enabled, fraction 0 (insertion offset)", mid, sd, fs)
            delays = {}
            for j, lab in enumerate("BCD"):
                if lab not in labs:
                    continue
                ins = mid[j] - before[j]
                need = need_samples(before[j])
                delays[lab] = plan(need, ins, SLOPE_NS, fs, fmax)
                print(f"  {lab}: needs {need / fs * 1e9:.2f} ns, enable alone gives "
                      f"{ins / fs * 1e9:.2f} ns -> {delays[lab] or 'out of reach, bypassed'}")
                if delays[lab] is None:
                    delays[lab] = (0, False)

        apply_delays(dev, delays)
        touched |= set(delays)
        time.sleep(args.settle)
        after, sd = averaged(dev, args.tone, args.captures)
        report("after", after, sd, fs)

        if args.auto:
            # Refine with each channel's own measured slope above the insertion offset.
            refined = {}
            for j, lab in enumerate("BCD"):
                fr, en = delays.get(lab, (0, False))
                moved = after[j] - mid[j]
                if not en or not fr or not 0 < moved < 0.5:
                    continue
                slope = moved / fs * 1e9 / fr
                st = plan(need_samples(before[j]), mid[j] - before[j], slope, fs, fmax)
                if st and st != (fr, en):
                    refined[lab] = st
                print(f"  {lab}: measured {slope:.3f} ns/LSB -> {st}")
            if refined:
                apply_delays(dev, refined)
                time.sleep(args.settle)
                after, sd = averaged(dev, args.tone, args.captures)
                report("after refinement", after, sd, fs)

        print("\n  change vs before (samp): "
              + "  ".join(f"{c} {a - b:+.4f}" for c, a, b in zip("BCD", after, before0)))
        jumps = [c for c, a, b in zip("BCD", after, before0) if abs(a - b) > 0.5]
        if jumps:
            print(f"  *** whole-sample jump on {','.join(jumps)}: the clock shift moved the DMA start")
    finally:
        if not args.keep:
            for lab in touched:
                dev.set_clock_delay(lab, 0)
            for pair in phases:
                dev.set_clock_phase(pair, 0)
            print("\n  clocks restored (bypass" + (", phase 0 + sync" if phases else "") + ")")
        else:
            print(f"\n  kept: {dev.clock_delay}  (a reboot restores bypass)")


if __name__ == "__main__":
    main()
