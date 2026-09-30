# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 — check that inter-channel sync is stable, boot after boot.

Run this once per boot with the usual tone on J11.  It calibrates the alignment,
then re-measures the skew from a fresh capture to prove the correction actually
took, and appends one row per boot to a CSV so the boot-to-boot picture builds
up without anyone having to keep notes.

What it is testing
------------------
The FPGA re-draws each channel's BUFR /4 divider phase every time it is
configured, so B/C/D come up a whole number of samples behind A and the draw is
different on every boot (0/-1/-2/-3 samples = 0/8/16/24 ns).  TDD cannot see
this: it only lines up the DMA starts to within one adc_clk.  Pulsing the shared
SERDES reset was measured to leave 8.8-16.8 ns, so the fix is to measure the
draw and shift the buffers.

The 'removed' column is expected to change between boots -- that is the draw.
The 'residual' column is what matters: with sub-sample correction on it should be
a small number, the same one every boot, because the measured delay is taken out
in full rather than rounded to whole samples.

Usage:
  python3 ada4356_quad_sync_check.py ip:192.168.0.106
  python3 ada4356_quad_sync_check.py ip:192.168.0.106 --tone 100000 --trials 5
  python3 ada4356_quad_sync_check.py ip:192.168.0.106 --tag "cold boot"
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import numpy as np

import adi
from adi.ada4356_quad import CHANNEL_LABELS, _estimate_tone_hz, _tone_phase

TDD_CLOCK_HZ = 125_000_000
TDD_ON_BASE = 100
TDD_OFF_BASE = 200
FULL_SCALE = 8191

# With sub-sample correction on, the whole measured delay is removed, so what is
# left is interpolator and fit error, not the analog term.  Anything approaching
# a sample (8 ns) means the correction did not take.
ALIGNED_NS = 1.0


def setup_tdd(dev):
    """1 s frame, all four DMA syncs on the same pulse (as in the main example)."""
    tdd = dev.tdd
    tdd.enable = False
    tdd.burst_count = 0
    tdd.frame_length_raw = TDD_CLOCK_HZ
    tdd.channel[0].enable = False
    for ch_idx in range(1, 5):
        tdd.channel[ch_idx].on_raw = TDD_ON_BASE
        tdd.channel[ch_idx].off_raw = TDD_OFF_BASE
        tdd.channel[ch_idx].enable = True
    tdd.enable = True
    try:
        tdd.sync_soft = True
    except Exception:
        pass
    time.sleep(0.3)


def skew_ns(data, f0, fs):
    """Per-channel delay vs A, in ns, from the tone phase."""
    ref = _tone_phase(data[0], f0, fs)
    out = []
    for x in data:
        dphi = (ref - _tone_phase(x, f0, fs) + np.pi) % (2 * np.pi) - np.pi
        out.append(dphi / (2 * np.pi) * (fs / f0) / fs * 1e9)
    return out


def check_clipping(data):
    """Clipping fakes a -65 dBc harmonic comb and wrecks the phase fit, so it has
    to be ruled out before any skew number is believed."""
    hits = []
    for label, x in zip(CHANNEL_LABELS, data):
        if x.max() >= FULL_SCALE or x.min() <= -FULL_SCALE - 1:
            hits.append(f"{label} (max {int(x.max())}, min {int(x.min())})")
    return hits


def main():
    ap = argparse.ArgumentParser(
        description="Check inter-channel sync stability across boots."
    )
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.106")
    ap.add_argument("--samples", type=int, default=65536)
    ap.add_argument("--tone", type=float, default=100e3, help="generator tone, Hz")
    ap.add_argument(
        "--trials",
        type=int,
        default=3,
        help="re-calibrations in this boot; they must all agree",
    )
    ap.add_argument("--tag", default="", help="note for the log, e.g. 'cold boot'")
    ap.add_argument(
        "--log",
        default=os.path.expanduser("~/ada4356_sync_log.csv"),
        help="CSV appended to on every run",
    )
    args = ap.parse_args()

    print(f"Connecting to {args.uri} ...")
    dev = adi.ada4356_quad(uri=args.uri)
    dev.rx_buffer_size = args.samples
    fs = dev.sampling_frequency
    setup_tdd(dev)
    print(f"  fs {fs / 1e6:.3f} MHz, {args.samples} samples, tone {args.tone / 1e3:.1f} kHz")

    rows = []
    for trial in range(args.trials):
        cal = dev.calibrate_alignment(args.tone, verbose=False)
        removed = [cal["removed_samples"][c] for c in CHANNEL_LABELS]

        # Re-capture through rx() so the correction is verified, not assumed.
        data = [x.astype(np.float64) for x in dev.rx()]
        clipped = check_clipping(data)
        f0 = _estimate_tone_hz(data[0], args.tone, fs)
        resid = skew_ns(data, f0, fs)
        spread = max(resid) - min(resid)

        rows.append(
            {
                "removed": removed,
                "resid": resid,
                "spread": spread,
                "clipped": clipped,
            }
        )

        if trial == 0:
            print(f"\n  tone fitted to {f0 / 1e3:.4f} kHz")
            if clipped:
                print("  *** CLIPPING on " + ", ".join(clipped))
                print("  *** lower the generator; skew and THD are meaningless now")
            print(
                f"\n  {'trial':>5}  {'removed (samp)':>18}  "
                f"{'residual skew vs A (ns)':>34}  {'spread':>8}"
            )
            print(
                f"  {'':>5}  {'A   B   C   D':>18}  "
                f"{'A       B       C       D':>34}  {'(ns)':>8}"
            )

        rem_s = " ".join(f"{v:>3d}" for v in removed)
        res_s = " ".join(f"{v:>7.2f}" for v in resid)
        print(f"  {trial:>5}  {rem_s:>18}  {res_s:>34}  {spread:>8.2f}")

    # --- verdict -----------------------------------------------------------
    print()
    all_removed = [tuple(r["removed"]) for r in rows]
    worst_spread = max(r["spread"] for r in rows)
    mean_resid = [float(np.mean([r["resid"][i] for r in rows])) for i in range(4)]
    any_clipped = any(r["clipped"] for r in rows)

    stable_in_boot = len(set(all_removed)) == 1
    if stable_in_boot:
        print(f"  offsets repeatable within this boot: {all_removed[0]}")
    else:
        print("  *** offsets CHANGED between trials in the same boot:")
        for r in all_removed:
            print(f"        {r}")
        print("  *** nothing should re-phase the divider while the board is up;")
        print("  *** suspect a marginal tone (low amplitude) or an unstable fit")

    if any_clipped:
        print("  *** VERDICT WITHHELD: the capture clipped, so the phase fit is")
        print("  *** distorted and this run is not evidence either way.")
        print("  *** Lower the generator and re-run before logging a result.")
    elif worst_spread <= ALIGNED_NS:
        print(f"  residual spread {worst_spread:.2f} ns -- channels are aligned.")
    elif worst_spread < 8.0:
        print(f"  residual spread {worst_spread:.2f} ns -- more than expected but")
        print("     under one sample; check the tone level and re-run.")
    else:
        print(f"  *** residual spread {worst_spread:.2f} ns is a sample or more.")
        print("  *** the correction did not take; do not trust this capture.")

    # --- log ---------------------------------------------------------------
    new = not os.path.exists(args.log)
    with open(args.log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(
                ["timestamp", "tag", "tone_hz", "samples"]
                + [f"removed_{c}" for c in CHANNEL_LABELS]
                + [f"resid_ns_{c}" for c in CHANNEL_LABELS]
                + ["spread_ns", "stable_in_boot", "clipped"]
            )
        w.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                args.tag,
                f"{args.tone:.0f}",
                args.samples,
            ]
            + list(all_removed[0])
            + [f"{v:.3f}" for v in mean_resid]
            + [f"{worst_spread:.3f}", int(stable_in_boot), int(any_clipped)]
        )
    print(f"\n  appended to {args.log}")

    # --- history -----------------------------------------------------------
    with open(args.log) as fh:
        hist = list(csv.DictReader(fh))
    if len(hist) > 1:
        print(f"\n=== {len(hist)} runs logged so far ===")
        print(
            f"  {'when':>16}  {'tag':<12}  {'removed':>13}  "
            f"{'spread':>7}  {'resid B/C/D (ns)':>22}"
        )
        for h in hist[-10:]:
            rem = " ".join(f"{h['removed_' + c]:>3}" for c in CHANNEL_LABELS)
            res = " ".join(f"{float(h['resid_ns_' + c]):>6.2f}" for c in "BCD")
            flag = "  clipped" if h.get("clipped") == "1" else ""
            print(
                f"  {h['timestamp'][5:16]:>16}  {h['tag'][:12]:<12}  {rem:>13}  "
                f"{float(h['spread_ns']):>7.2f}  {res:>22}{flag}"
            )

        good = [h for h in hist if h.get("clipped") != "1"]
        skipped = len(hist) - len(good)
        if skipped:
            print(f"\n  {skipped} clipped run(s) excluded from the summary below")
        if not good:
            print("  no usable runs yet -- every logged run clipped")
            return

        draws = {tuple(h["removed_" + c] for c in CHANNEL_LABELS) for h in good}
        spreads = [float(h["spread_ns"]) for h in good]
        print(f"\n  {len(draws)} distinct divider draws seen across {len(good)} runs")
        print(
            f"  residual spread over all runs: "
            f"{min(spreads):.2f} .. {max(spreads):.2f} ns"
        )
        if len(draws) < 2:
            print("  -> only one draw seen so far; reboot and re-run to prove the")
            print("     correction tracks a *different* draw.")
        elif max(spreads) <= ALIGNED_NS:
            print("  -> the draw changed between boots and the residual did not.")
            print("     That is the fix working.")
        else:
            print("  -> at least one run exceeded the expected spread; inspect that row.")


if __name__ == "__main__":
    sys.exit(main())
