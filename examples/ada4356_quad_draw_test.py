# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 — automated whole-sample draw test, one CSV row per capture.

Two modes, both uncorrected (no calibrate_alignment()), both with the usual
tone on J11:

  boots  Reboot the board over SSH N times.  After each boot read every core's
         frame-aligner status (shift_cnt, lock, re-lock count) and IDELAY taps
         straight from the FPGA, capture once, and log the skew of B/C/D vs A
         split into whole samples + fixed fraction.  A warm reboot reconfigures
         the FPGA exactly like a power cycle (measured), so each boot is a new
         BUFR draw.  Needs key-based SSH to root on the board, set up once with
         `ssh-copy-id root@<board>`; BatchMode means it never prompts.

  sweep  Inside one boot, step the AD9517 fine delay of one ADC clock
         (OUT4..OUT7 = A..D) and capture K times per step.  A whole-sample
         jump in one channel at a delay threshold is the signature of the DMA
         start pulse crossing from A's clock into that channel's clock.  The
         output is always put back in bypass on exit.

  boots-sweep  Both: reboot, sweep, reboot, sweep ... and report per boot
         whether any channel's whole-sample value changed during its sweep.

  once   No reboot: read status and capture --count times on the running boot.
         Use after a manual power cycle.

Usage:
  python3 ada4356_quad_draw_test.py boots ip:192.168.0.102 --count 10 --tag 4dco
  python3 ada4356_quad_draw_test.py once ip:192.168.0.102 --count 3 --tag shared-pc
  python3 ada4356_quad_draw_test.py sweep ip:192.168.0.102 --out A --captures 2
  python3 ada4356_quad_draw_test.py boots-sweep ip:192.168.0.102 --count 5
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime

import numpy as np

import adi
from adi.ada4356_quad import CHANNEL_LABELS, _estimate_tone_hz

TDD_CLOCK_HZ = 125_000_000
PCORE = 0x80000000  # cf_axi_adc debugfs: route the access to the AXI core, not SPI
ALIGN_STATUS = 0xCC
IDELAY_BASE = 0x800
AD9517_DELAY_BASE = 0xA0  # OUTn bypass/full-scale/fraction at 0xA0 + 3*(n-4)
AD9517_MAX_FRACTION = 47  # datasheet: larger fractions are unsupported
FULL_SCALE = 8191


def connect(uri, timeout_s):
    t0 = time.time()
    while True:
        try:
            return adi.ada4356_quad(uri=uri)
        except Exception:
            if time.time() - t0 > timeout_s:
                raise
            time.sleep(5)


def setup(dev, args):
    # Both setters move the front-end group delay, so they go before anything else.
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


def core_status(ctx):
    """Per channel: shift_cnt, locked, re-lock count, frame-lane IDELAY tap.

    Pre-shift_cnt bitstreams read the status register as 0, i.e. 'locked 0'.
    """
    out = []
    for lab in CHANNEL_LABELS:
        d = ctx.find_device(f"ada4356-{lab.lower()}")
        st = d.reg_read(PCORE | ALIGN_STATUS)
        tap = d.reg_read(PCORE | (IDELAY_BASE + 8))
        out.append((st & 0x7, (st >> 3) & 1, (st >> 8) & 0xFF, tap & 0x1F))
    return out


def sine_fit(x, f0, fs):
    """DC and phase of x = dc + R*cos(2*pi*f0*n/fs + phase).

    Fitted jointly: with 52.43 cycles in the buffer a plain mean carries part of
    a cycle, which biases both the DC (+-35 codes) and the phase (~0.05 samp).
    """
    w = 2 * np.pi * f0 / fs * np.arange(x.size)
    m = np.column_stack([np.ones_like(w), np.cos(w), np.sin(w)])
    dc, a, b = np.linalg.lstsq(m, x, rcond=None)[0]
    return dc, np.arctan2(-b, a)


def measure(dev, tone):
    data = [np.asarray(x, dtype=np.float64) for x in dev.rx()]
    fs = dev.sampling_frequency
    f0 = _estimate_tone_hz(data[0], tone, fs)
    fits = [sine_fit(x, f0, fs) for x in data]
    ph = [p for _, p in fits]
    # Same sign as ada4356_quad_example.py: negative = channel lags A.
    skew = [((p - ph[0] + np.pi) % (2 * np.pi) - np.pi) / (2 * np.pi) * fs / f0
            for p in ph[1:]]
    clipped = any(x.max() >= FULL_SCALE or x.min() <= -FULL_SCALE - 1 for x in data)
    return skew, float(fits[0][0]), clipped


def ssh_reboot(host):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
         f"root@{host}", "reboot"],
        capture_output=True, text=True, timeout=30)
    if "Permission denied" in r.stderr or "Host key verification" in r.stderr:
        sys.exit(f"SSH to root@{host} failed:\n{r.stderr.strip()}\n"
                 f"Run `ssh-copy-id root@{host}` once (and accept the host key), then retry.")


def wait_down(host, timeout_s=60):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if subprocess.run(["ping", "-c", "1", "-W", "1", host],
                          capture_output=True).returncode != 0:
            return
        time.sleep(1)
    sys.exit(f"{host} never went down after 'reboot' -- the board did not reboot")


class Log:
    FIELDS = (["timestamp", "mode", "tag", "step", "out", "fraction", "ped_A", "clipped"]
              + [f"shift_{c}" for c in CHANNEL_LABELS]
              + [f"locked_{c}" for c in CHANNEL_LABELS]
              + [f"relock_{c}" for c in CHANNEL_LABELS]
              + [f"tap_{c}" for c in CHANNEL_LABELS]
              + [f"skew_{c}" for c in "BCD"]
              + [f"n_{c}" for c in "BCD"])

    def __init__(self, path):
        new = not os.path.exists(path)
        self.fh = open(path, "a", newline="")
        self.w = csv.writer(self.fh)
        if new:
            self.w.writerow(self.FIELDS)
        self.path = path

    def row(self, mode, args, step, out, fraction, status, skew, ped, clipped, frac_ref):
        n = [int(round(s - f)) for s, f in zip(skew, frac_ref)]
        self.w.writerow(
            [datetime.now().isoformat(timespec="seconds"), mode, args.tag, step, out,
             fraction, f"{ped:.1f}", int(clipped)]
            + [s[0] for s in status] + [s[1] for s in status]
            + [s[2] for s in status] + [s[3] for s in status]
            + [f"{s:.4f}" for s in skew] + n)
        self.fh.flush()
        shifts = "".join(str(s[0]) for s in status)
        relock = sum(s[2] for s in status)
        unlocked = "".join(c for c, s in zip(CHANNEL_LABELS, status) if not s[1])
        flags = (" CLIPPED" if clipped else "") + (f" relock={relock}" if relock else "") \
            + (f" UNLOCKED {unlocked}" if unlocked else "")
        print(f"  {step:>5} {str(fraction):>4}  shift {shifts}  taps "
              + "/".join(f"{s[3]:2d}" for s in status)
              + "  skew " + " ".join(f"{s:+8.4f}" for s in skew)
              + f"  n ({n[0]:+d},{n[1]:+d},{n[2]:+d})  pedA {ped:7.1f}{flags}")
        return tuple(n)


def boot_up(args, host):
    ssh_reboot(host)
    wait_down(host)
    dev = connect(args.uri, args.boot_timeout)
    time.sleep(args.settle)
    setup(dev, args)
    return dev


def run_boots(args, log, frac_ref):
    host = args.uri.split(":", 1)[1]
    states = []
    for i in range(args.count):
        print(f"\n[{i + 1}/{args.count}] rebooting {host} ...", flush=True)
        dev = boot_up(args, host)
        status = core_status(dev.ch_a._ctx)
        skew, ped, clipped = measure(dev, args.tone)
        states.append(log.row("boots", args, i + 1, "", "", status, skew, ped, clipped, frac_ref))
        del dev

    print(f"\n=== {len(states)} boots ===")
    for st, k in Counter(states).most_common():
        print(f"  (B,C,D) = ({st[0]:+d},{st[1]:+d},{st[2]:+d})  x{k}")
    for j, c in enumerate("BCD"):
        print(f"  {c}: whole-sample values seen {sorted({s[j] for s in states})}")


def run_once(args, log, frac_ref):
    dev = connect(args.uri, 10)
    setup(dev, args)
    ctx = dev.ch_a._ctx
    for i in range(args.count):
        status = core_status(ctx)
        skew, ped, clipped = measure(dev, args.tone)
        log.row("once", args, i + 1, "", "", status, skew, ped, clipped, frac_ref)


def run_sweep(args, log, frac_ref, dev=None, mode="sweep"):
    """Returns ([(fraction, state)], finished); finished is False if the board stopped."""
    fracs = [int(f, 0) for f in args.fractions.split(",")]
    if max(fracs) > AD9517_MAX_FRACTION:
        sys.exit(f"fractions above {AD9517_MAX_FRACTION} are unsupported by the AD9517")
    if dev is None:
        dev = connect(args.uri, 10)
        setup(dev, args)
    ctx = dev.ch_a._ctx
    ad = ctx.find_device("ad9517-4")
    base = AD9517_DELAY_BASE + 3 * CHANNEL_LABELS.index(args.out)

    states = []
    finished = False
    try:
        ad.reg_write(base + 2, fracs[0])
        ad.reg_write(base + 1, args.full_scale)
        ad.reg_write(base, 0)
        for fr in fracs:
            ad.reg_write(base + 2, fr)
            time.sleep(args.settle)
            for k in range(args.captures):
                status = core_status(ctx)
                skew, ped, clipped = measure(dev, args.tone)
                states.append((fr, log.row(mode, args, k + 1, args.out, fr, status,
                                           skew, ped, clipped, frac_ref)))
        finished = True
    except Exception as exc:
        print(f"\n*** stopped: {exc!r}")
        print("*** if the board stopped answering, power-cycle it; the delay resets to bypass")
    finally:
        try:
            ad.reg_write(base, 1)
            print(f"\n  OUT{4 + CHANNEL_LABELS.index(args.out)} ({args.out}) back to bypass")
        except Exception:
            pass

    if states and mode == "sweep":
        print("\n=== whole-sample state per fraction ===")
        for fr in fracs:
            seen = sorted({s for f, s in states if f == fr})
            if seen:
                print(f"  {fr:>3}: " + ", ".join(f"({s[0]:+d},{s[1]:+d},{s[2]:+d})" for s in seen))
    return states, finished


def flips(states):
    """Channels whose whole-sample value changed during one sweep, with where."""
    out = []
    for j, c in enumerate("BCD"):
        if len({s[j] for _, s in states}) > 1:
            first = states[0][1][j]
            at, new = next((f, s[j]) for f, s in states if s[j] != first)
            out.append(f"{c} {first:+d}->{new:+d} at fraction {at}")
    return out


def run_boots_sweep(args, log, frac_ref):
    host = args.uri.split(":", 1)[1]
    results = []
    for i in range(args.count):
        print(f"\n[{i + 1}/{args.count}] rebooting {host} ...", flush=True)
        dev = boot_up(args, host)
        states, finished = run_sweep(args, log, frac_ref, dev, mode="boots-sweep")
        del dev
        f = flips(states)
        results.append((i + 1, states[0][1] if states else None, f))
        print(f"  boot {i + 1}: " + ("; ".join(f) if f else "no whole-sample change"))
        if not finished:
            print("*** board stopped answering; ending the run here")
            break

    print(f"\n=== {len(results)} boots swept, {args.out} delay fractions {args.fractions} ===")
    for b, s0, f in results:
        start = f"({s0[0]:+d},{s0[1]:+d},{s0[2]:+d})" if s0 else "-"
        print(f"  boot {b:>2}  start {start}  " + ("; ".join(f) if f else "no change"))
    n_flip = sum(1 for _, _, f in results if f)
    print(f"  boots with a whole-sample jump during the sweep: {n_flip}/{len(results)}")


def main():
    ap = argparse.ArgumentParser(description="Automated whole-sample draw test.")
    ap.add_argument("mode", choices=["boots", "sweep", "boots-sweep", "once"])
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.102")
    ap.add_argument("--samples", type=int, default=65536)
    ap.add_argument("--tone", type=float, default=100e3)
    ap.add_argument("--gain", default="11k")
    ap.add_argument("--filter", default="fsel1")
    ap.add_argument("--frac-ref", default="-0.07,0.53,-0.05",
                    help="fixed B,C,D fractions (samples) used to split off the whole "
                         "part; measured 2026-10-13 at 11k / 200R / fsel1")
    ap.add_argument("--tag", default="")
    ap.add_argument("--log", default=os.path.expanduser("~/ada4356_draw_log.csv"))
    ap.add_argument("--settle", type=float, default=2.0, help="s after boot / delay write")
    # boots
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--boot-timeout", type=float, default=240.0)
    # sweep
    ap.add_argument("--out", choices=CHANNEL_LABELS, default="A")
    ap.add_argument("--full-scale", type=lambda s: int(s, 0), default=0x39,
                    help="AD9517 0xA1-style ramp register; 0x39 measured ~0.045-0.06 ns/LSB")
    # 44 and 47 froze the board once each with 0x39; likely past the AD9517 half-period limit.
    ap.add_argument("--fractions", default="0,2,4,6,8,12,16,20,24,28,32,36")
    ap.add_argument("--captures", type=int, default=2)
    args = ap.parse_args()

    frac_ref = [float(v) for v in args.frac_ref.split(",")]
    log = Log(args.log)
    print(f"logging to {log.path}")
    print(f"  {'step':>5} {'frac':>4}  shift ABCD  taps A/B/C/D      skew B / C / D (samp)"
          f"          state")
    if args.mode == "boots":
        run_boots(args, log, frac_ref)
    elif args.mode == "sweep":
        run_sweep(args, log, frac_ref)
    elif args.mode == "once":
        run_once(args, log, frac_ref)
    else:
        run_boots_sweep(args, log, frac_ref)


if __name__ == "__main__":
    main()
