# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 — try to prove the channel alignment WRONG.

Checking the alignment at the same tone it was calibrated with cannot fail: the
buffers are shifted by exactly the measured delay, so re-measuring returns zero
by construction.  That is not evidence.  Neither is cross-correlation, which on a
clean sine is algebraically the same estimate as the DFT phase.

This script separates the two steps so the second one can disagree with the
first:

  1. --save : calibrate at the current tone and write the offsets to a file.
  2. change the generator to a different frequency.
  3. --load : apply the stored offsets WITHOUT re-measuring, and report the skew.

Step 3 uses data the correction was never fitted to.  A delay is a delay at every
frequency, so if the alignment is real the skew stays near zero.  If step 1 was
nulling something specific to that tone, step 3 is where it shows up.

A second, independent estimator (interpolated zero crossings, measured in the
time domain rather than from a transform) runs alongside the DFT phase.  They
lean on different properties of the signal, so a disagreement between them is
itself a warning.

Usage:
  # generator at 100 kHz
  python3 ada4356_quad_verify_alignment.py ip:192.168.0.106 --tone 100000 --save /tmp/cal.json

  # now set the generator to 300 kHz, leave everything else alone
  python3 ada4356_quad_verify_alignment.py ip:192.168.0.106 --tone 300000 --load /tmp/cal.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np

import adi
from adi.ada4356_quad import CHANNEL_LABELS, _estimate_tone_hz, _tone_phase

TDD_CLOCK_HZ = 125_000_000
FULL_SCALE = 8191


def setup_tdd(dev):
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


def skew_by_phase(data, f0, fs):
    """Delay vs A in ns, from the DFT phase -- the same estimator the
    calibration uses, kept here as the baseline to compare against."""
    ref = _tone_phase(data[0], f0, fs)
    out = []
    for x in data:
        dphi = (ref - _tone_phase(x, f0, fs) + np.pi) % (2 * np.pi) - np.pi
        out.append(dphi / (2 * np.pi) * (fs / f0) / fs * 1e9)
    return out


def mean_crossing_time(x, fs, f0):
    """Average time of the rising mean-crossings, in seconds.

    Time domain and waveform-agnostic, so it also works on a square wave, which
    the DFT-phase estimator would read through its fundamental only.
    """
    v = x - x.mean()
    rising = np.flatnonzero((v[:-1] <= 0) & (v[1:] > 0))
    if rising.size < 4:
        return None
    # Linear interpolation between the bracketing samples.
    frac = -v[rising] / (v[rising + 1] - v[rising])
    t = (rising + frac) / fs
    # Fold onto one period so the mean is not dominated by which crossing is
    # first; the crossings are one period apart by construction.
    period = 1.0 / f0
    phase = np.mod(t, period)
    # Circular mean, so a cluster straddling 0 does not average to mid-period.
    ang = 2 * np.pi * phase / period
    return np.angle(np.mean(np.exp(1j * ang))) / (2 * np.pi) * period


def skew_by_crossing(data, f0, fs):
    """Delay vs A in ns, from interpolated zero crossings."""
    ref = mean_crossing_time(data[0], fs, f0)
    if ref is None:
        return None
    period_ns = 1e9 / f0
    out = []
    for x in data:
        t = mean_crossing_time(x, fs, f0)
        if t is None:
            return None
        d = (t - ref) * 1e9
        out.append((d + period_ns / 2) % period_ns - period_ns / 2)
    return out


def tone_is_present(x, f0, fs):
    """Is f0 really the fundamental, or did the search settle on a harmonic?

    Asking for 200 kHz while the generator is still at 100 kHz lands on H2, which
    is 70-80 dB down but still the local peak, and the calibration that follows
    would be quietly meaningless.  A sine puts amplitude at std*sqrt(2).
    """
    n = np.arange(x.size)
    v = x - x.mean()
    amp = 2 * abs(np.dot(v, np.exp(-2j * np.pi * f0 * n / fs))) / x.size
    expected = v.std() * np.sqrt(2)
    return amp > 0.3 * expected, amp, expected


def main():
    ap = argparse.ArgumentParser(
        description="Cross-check the alignment against data it was not fitted to."
    )
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.106")
    ap.add_argument("--tone", type=float, required=True, help="generator tone now, Hz")
    ap.add_argument("--samples", type=int, default=65536)
    ap.add_argument("--save", metavar="FILE", help="calibrate now and store it")
    ap.add_argument("--load", metavar="FILE", help="apply a stored calibration as-is")
    args = ap.parse_args()

    if bool(args.save) == bool(args.load):
        ap.error("use exactly one of --save or --load")

    dev = adi.ada4356_quad(uri=args.uri)
    dev.rx_buffer_size = args.samples
    fs = dev.sampling_frequency
    setup_tdd(dev)
    print(f"Connected. fs {fs / 1e6:.3f} MHz, tone {args.tone / 1e3:.1f} kHz")

    if args.save:
        if os.path.exists(args.save):
            try:
                with open(args.save) as fh:
                    old = json.load(fh)
                if abs(old["tone_hz"] / args.tone - 1) > 0.05:
                    print(f"\n  *** {args.save} already holds a calibration taken at")
                    print(f"  *** {old['tone_hz'] / 1e3:.1f} kHz. Overwriting it at "
                          f"{args.tone / 1e3:.1f} kHz destroys the")
                    print("  *** cross-frequency check -- you almost certainly meant --load.")
                    print("  *** Re-run with --load to test, or --save to a new file.")
                    return 1
            except (KeyError, ValueError):
                pass

        cal = dev.calibrate_alignment(args.tone, verbose=False)

        check = [x.astype(np.float64) for x in dev.rx()]
        ok, amp, expected = tone_is_present(check[0], cal["tone_hz"], fs)
        if not ok:
            print(f"\n  *** The tone at {cal['tone_hz'] / 1e3:.1f} kHz is only {amp:.0f} "
                  f"codes where {expected:.0f} was expected.")
            print("  *** That is a harmonic or noise, not the fundamental -- check the")
            print("  *** generator is actually set to this frequency. Not saving.")
            return 1

        payload = {
            "tone_hz": cal["tone_hz"],
            "offsets": [cal["removed_samples"][c] for c in CHANNEL_LABELS],
            "frac": [cal["residual_samples"][c] for c in CHANNEL_LABELS],
        }
        with open(args.save, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"  calibrated at {payload['tone_hz'] / 1e3:.4f} kHz")
        print(f"  offsets {payload['offsets']}")
        print(f"  frac    {[round(v, 4) for v in payload['frac']]}")
        print(f"  saved to {args.save}")
        print("\n  Now change the generator to a different frequency and re-run")
        print(f"  with --load {args.save} --tone <new frequency>.")
        return 0

    with open(args.load) as fh:
        payload = json.load(fh)
    dev.set_alignment(payload["offsets"], payload["frac"])
    cal_tone = payload["tone_hz"]
    print(f"  applied calibration from {cal_tone / 1e3:.4f} kHz, "
          f"offsets {payload['offsets']}")

    ratio = args.tone / cal_tone
    if 0.95 < ratio < 1.05:
        print("\n  *** This is the same tone the calibration was taken at, so the")
        print("  *** check is circular and cannot fail. Change the generator.")

    data = [x.astype(np.float64) for x in dev.rx()]

    clipped = [c for c, x in zip(CHANNEL_LABELS, data)
               if x.max() >= FULL_SCALE or x.min() <= -FULL_SCALE - 1]
    if clipped:
        print(f"\n  *** CLIPPING on {', '.join(clipped)} -- lower the generator;")
        print("  *** the phase fit is distorted and this result means nothing.")
        return 1

    f0 = _estimate_tone_hz(data[0], args.tone, fs)
    ok, amp, expected = tone_is_present(data[0], f0, fs)
    if not ok:
        print(f"\n  *** The tone at {f0 / 1e3:.1f} kHz is only {amp:.0f} codes where")
        print(f"  *** {expected:.0f} was expected -- that is a harmonic, not the")
        print("  *** fundamental. Set the generator to this frequency and re-run.")
        return 1

    print(f"  tone fitted to {f0 / 1e3:.4f} kHz "
          f"({ratio:.2f}x the calibration tone)")

    ph = skew_by_phase(data, f0, fs)
    zc = skew_by_crossing(data, f0, fs)

    print(f"\n  {'Ch':>3}  {'DFT phase (ns)':>15}  {'zero crossings (ns)':>21}")
    for i, c in enumerate(CHANNEL_LABELS):
        z = f"{zc[i]:.2f}" if zc else "n/a"
        print(f"  {c:>3}  {ph[i]:>15.2f}  {z:>21}")

    worst = max(ph) - min(ph)
    print(f"\n  spread, DFT phase      : {worst:.2f} ns")
    if zc:
        zw = max(zc) - min(zc)
        print(f"  spread, zero crossings : {zw:.2f} ns")
        if abs(zw - worst) > 2.0:
            print("  *** the two estimators disagree by more than 2 ns, so at least")
            print("  *** one of them is being misled. Do not trust either number.")

    one_sample_ns = 1e9 / fs
    print()
    if worst <= 1.0:
        print(f"  {worst:.2f} ns at a tone the calibration never saw.")
        print("  A frequency-specific artefact would not survive this, so the")
        print("  correction is behaving as a real delay.")
    elif worst < one_sample_ns:
        print(f"  {worst:.2f} ns -- under one sample ({one_sample_ns:.1f} ns) but")
        print("  well above the same-tone result. Something is frequency")
        print("  dependent: suspect a front-end pole difference, not the draw.")
    else:
        print(f"  *** {worst:.2f} ns is a whole sample or more. The alignment does")
        print("  *** NOT hold at this frequency, so the same-tone result was")
        print("  *** measuring itself. Treat the fix as unproven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
