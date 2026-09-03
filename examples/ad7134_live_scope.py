#!/usr/bin/env python3
# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Live 8-channel raw scope + before/after multidevice sync capture.

Holds one DMA buffer open and refills it continuously, drawing all eight
channels as raw ADC counts and tracking the device-to-device phase match.

    0..3 -> adc_0 (die A)      4..7 -> adc_1 (die B)

Two modes:

  single phase   run for --minutes, optionally syncing once at the start
  --sync-compare run --minutes, issue DIG_IF_RESET once, run --minutes again

Each run creates its own folder, so nothing needs to be passed on the command
line and two runs never mix:

  ad7134_<stamp>/
      before_sync_phase.csv   die-to-die phase vs time, one row per refill,
                              the whole unsynced phase
      after_sync_phase.csv    the same for the whole synced phase
      before_sync_raw.csv     raw counts, the last buffer before the sync
      after_sync_raw.csv      raw counts, the first buffer after it

So _phase is the continuous record and _raw is the waveform evidence at the
sync instant. The two raw files are one --window buffer each, captured either
side of the DIG_IF_RESET with nothing in between, so they can be compared
directly; both replay through ad7134_phase_from_csv.py. Single-phase mode has
no sync boundary and writes only run_phase.csv.

--outdir picks the parent of that folder; it defaults to the current directory.

Why raw is dumped in discrete buffers rather than streamed: 1 s of 8-channel
raw is 86.8 MB of CSV and takes ~3 s to write, so continuous raw CSV can never
keep up with a 1.3 MSPS ADC. The phase CSV covers the whole run; the raw dumps
give real waveforms to re-analyse, at a disk cost you set with --window.
--grab-every adds extra dumps through a phase if you want them.

Keys:  s = grab raw now    p = pause    q = quit early

Run from the examples/ directory (it imports ad7134_drift_monitor).

    python3 ad7134_live_scope.py ip:<board> --odr 1400000 --minutes 5 \
        --sync-compare --interval 30 --window 65536

Drive the generator at 20 kHz, not 250 kHz: at 250 kHz the cross-correlation
alias period is only ~5 samples, which makes the lag readout meaningless and
wraps the phase readout every 4 us.

No board? Everything works against a synthetic source with a known answer.
This one fakes a one-sample slip that the sync then removes:

    python3 ad7134_live_scope.py --demo --sync-compare --minutes 0.5 \
        --demo-delay-ns 779 --demo-delay-after-ns 8
"""

import argparse
import os
import shutil
import sys
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from ad7134_drift_monitor import (coarse_lag, cross_delays_ns, decode,
                                  find_device, read_status, show_status,
                                  trigger_sync)

import iio

SPEC_NS = 10.0
DEMO_FS = 48e6 / 37          # 1297297.3 Hz, the real rate behind a 1.3 MHz request
CSV_BYTES_PER_ROW = 66       # measured: 8 signed 24-bit columns plus separators
COLORS = ["#0d3b66", "#1f6fb2", "#4a9fd8", "#8ec9ee",    # die A
          "#7a1f1f", "#c0392b", "#e07b6a", "#f2b8ad"]    # die B


# ----------------------------------------------------------------- sources

def _odr_attr(dev):
    """sampling_frequency sits on the device on current kernels, and on the
    channels on kernels predating ADI commit 3a5bf2d8efed
    (ad4134_offload_attribute_group). Search both rather than assume."""
    if "sampling_frequency" in dev.attrs:
        return dev.attrs["sampling_frequency"]
    for c in dev.channels:
        if "sampling_frequency" in c.attrs:
            return c.attrs["sampling_frequency"]
    sys.exit("no sampling_frequency attribute on the device or its channels")


class HwSource:
    """Continuous capture: the buffer is created once and refilled for the
    whole run, which is what iio-oscilloscope does by default."""

    def __init__(self, uri, window, crc, odr=None):
        self.crc = crc
        self.ctx = iio.Context(uri)
        self.dev, self.chans = find_device(self.ctx)
        print(f"device: {self.dev.name}  ({len(self.chans)} scan elements)")
        if len(self.chans) < 8:
            print("WARNING: fewer than 8 scan elements - not the dual-die build.")

        attr = _odr_attr(self.dev)
        if odr:
            attr.value = str(odr)
            time.sleep(0.5)
        self.fs = float(attr.value)
        print(f"sampling_frequency: {self.fs:.1f} Hz  ({1e9 / self.fs:.2f} ns/sample)")

        for c in self.chans:
            c.enabled = True
        self.buf = iio.Buffer(self.dev, window)
        if self.buf is None:
            sys.exit("failed to create buffer - is iio-oscilloscope holding it?")

    def read(self):
        self.buf.refill()
        raws = [c.read(self.buf) for c in self.chans]
        sig = [decode(r, c.data_format, shift=8 if self.crc else None)
               for r, c in zip(raws, self.chans)]
        n = min(len(s) for s in sig)
        return [s[:n] for s in sig]

    def sync(self):
        trigger_sync(self.dev)
        time.sleep(0.5)
        for _ in range(3):       # frames already in the ring predate the reset
            self.buf.refill()

    def status(self, label):
        show_status(label, read_status(self.ctx))

    def close(self):
        pass


class DemoSource:
    """Synthetic 8 channels with an exact, known inter-die delay, so the
    display, the phase math and the file plumbing can be checked without
    hardware. sync() switches to delay_after_ns, faking a successful sync."""

    def __init__(self, window, fs, tone, delay_ns, delay_after_ns,
                 noise_db=-75.0, amp=6.0e6):
        self.window, self.fs, self.tone = window, fs, tone
        self.delay_s = delay_ns * 1e-9
        self.delay_after_s = delay_after_ns * 1e-9
        self.amp = amp
        self.sigma = amp * 10 ** (noise_db / 20.0)
        self.rng = np.random.default_rng()
        self.n0 = 0
        print(f"DEMO source: fs {fs:.1f} Hz, tone {tone:.1f} Hz, inter-die delay "
              f"{delay_ns:+.2f} ns before sync, {delay_after_ns:+.2f} ns after")

    def read(self):
        t = (self.n0 + np.arange(self.window)) / self.fs
        self.n0 += self.window
        time.sleep(self.window / self.fs)     # play back at real time
        out = []
        for ch in range(8):
            d = self.delay_s if ch >= 4 else 0.0
            x = self.amp * np.sin(2 * np.pi * self.tone * (t - d))
            out.append(x + self.rng.normal(0.0, self.sigma, self.window))
        return out

    def sync(self):
        print("sync triggered (DEMO - switching to the post-sync delay)")
        self.delay_s = self.delay_after_s

    def status(self, label):
        pass

    def close(self):
        pass


# ----------------------------------------------------------------- files

def grab_raw(src, need):
    """Refill back to back until `need` contiguous samples are collected.

    Nothing else runs during a grab, so the record has no gaps in it. The
    stream does gap *around* the grab while the file is written - that is the
    price of raw CSV, and the reason a grab is a discrete event rather than a
    continuous dump.
    """
    chunks, got = [], 0
    while got < need:
        s = src.read()
        chunks.append(s)
        got += len(s[0])
    nch = len(chunks[0])
    return [np.concatenate([c[i] for c in chunks])[:need] for i in range(nch)]


def write_raw_csv(path, sig):
    np.savetxt(path, np.column_stack([s.astype(np.int64) for s in sig]),
               delimiter=",", fmt="%d")
    return os.path.getsize(path)


def do_grab(src, n, fs, path, why):
    """Capture n samples of raw and write them, announcing both ends of it."""
    print(f"  ... {why}: grabbing {n} samples ({n / fs:.3f} s) -> {path}",
          flush=True)
    raw = grab_raw(src, n)
    sz = write_raw_csv(path, raw)
    print(f"  ... wrote {path}  ({sz / 1e6:.1f} MB, "
          f"{len(raw[0])} samples x {len(raw)} ch)", flush=True)
    return path


class MeasLog:
    """One row per refill, flushed as it goes so a long run survives a crash."""

    def __init__(self, path, nch):
        self.path = path
        self.f = open(path, "w")
        self.f.write("t_s,cross_ns,intra_die_spread_ns,coarse_lag,tone_hz,snr_db,"
                     + ",".join(f"ch{i}_ns" for i in range(nch)) + "\n")
        self.rows = 0
        self._next_flush = 0.0

    def row(self, t, cross, spread, lag, tone, snr, d):
        self.f.write(f"{t:.3f},{cross:.4f},{spread:.4f},{lag},{tone:.3f},{snr:.2f},"
                     + ",".join(f"{v:.4f}" for v in d) + "\n")
        self.rows += 1
        if t >= self._next_flush:
            self.f.flush()
            self._next_flush = t + 2.0

    def close(self):
        self.f.close()


def check_budget(outdir, args, fs, n_phases):
    """Refuse to start a run that cannot fit on disk. A surprise ENOSPC nine
    minutes into a ten minute capture costs the whole capture."""
    periodic = (0 if args.grab_every <= 0
                else int(args.minutes * 60 / args.grab_every))
    # the two that bracket the sync
    around = 2 if n_phases == 2 else 0
    grabs = n_phases * periodic + around
    per_grab = args.window * CSV_BYTES_PER_ROW
    total = grabs * per_grab
    free = shutil.disk_usage(outdir).free
    print(f"disk budget: {grabs} raw dumps x {per_grab / 1e6:.0f} MB "
          f"({args.window} samples = {args.window / fs:.3f} s each) "
          f"= {total / 1e9:.2f} GB "
          f"({free / 1e9:.1f} GB free in {os.path.abspath(outdir)})")
    if total > free * 0.9:
        sys.exit("  refusing to start: that does not fit. Lower --window, "
                 "raise --grab-every, or pick another --outdir.")
    if grabs:
        print(f"  each dump pauses the stream for ~{args.window * 2.4e-6:.1f} s "
              f"while the file is written")


# ----------------------------------------------------------------- display

def trigger_index(x):
    """First upward zero crossing of the DC-removed reference channel."""
    d = x - x.mean()
    up = np.flatnonzero((d[:-1] <= 0) & (d[1:] > 0))
    return int(up[0]) if len(up) else 0


def require_gui():
    if matplotlib.get_backend().lower() == "agg":
        sys.exit("matplotlib has no interactive backend (current: Agg).\n"
                 "  Use a display - ssh -X / ssh -Y - or set MPLBACKEND=TkAgg.")


class Scope:
    """The live window. Holds history across both phases so the before/after
    comparison is one continuous strip with the sync marked on it."""

    def __init__(self, total_s, args):
        self.args = args
        self.fig, (self.ax_tr, self.ax_hi) = plt.subplots(
            2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1]})
        self.fig.subplots_adjust(bottom=0.19, hspace=0.35)
        self.fig.suptitle("AD7134 live 8-channel raw scope    "
                          "[s] grab raw   [p] pause   [q] quit")

        self.lines = [self.ax_tr.plot([], [], lw=0.9, color=COLORS[i],
                                      label=f"ch{i}")[0] for i in range(8)]
        self.ax_tr.set_xlabel("Time (us)")
        self.ax_tr.set_ylabel("Raw ADC counts")
        self.ax_tr.grid(True, alpha=0.3)
        self.ax_tr.legend(ncol=8, fontsize=7, loc="upper right")

        self.hist_line, = self.ax_hi.plot([], [], "k-", lw=1.0)
        self.ax_hi.axhspan(-SPEC_NS, SPEC_NS, color="green", alpha=0.12)
        self.ax_hi.axhline(0.0, color="grey", lw=0.6)
        self.ax_hi.set_xlim(0, total_s)
        self.ax_hi.set_xlabel("Time (s)")
        self.ax_hi.set_ylabel("cross (ns)")
        self.ax_hi.set_title(
            f"die B avg - die A avg   (shaded = +/-{SPEC_NS:.0f} ns spec)", fontsize=9)
        self.ax_hi.grid(True, alpha=0.3)

        self.txt = self.fig.text(0.01, 0.01, "", family="monospace",
                                 fontsize=9, va="bottom")

        # matplotlib wraps any draw that lands more than a second after the
        # previous one in a "wait cursor" context, and the gtk3 set_cursor
        # ends with a *blocking* GLib main-loop iteration that only returns
        # when some X event shows up. Blitting makes full draws rare, so that
        # path is hit exactly at the interesting moments - the sync boundary -
        # where it stalled one phase for 32 s and silently truncated it. The
        # cursor is cosmetic here, so drop it.
        self.fig.canvas.set_cursor = lambda *_a, **_k: None

        # A full canvas redraw costs 80-190 ms on the gtk3agg backend, which
        # would cap the display near 5 fps on its own. Marking the moving
        # artists animated keeps them out of the cached background so each
        # frame only blits them.
        for a in [*self.lines, self.hist_line, self.txt]:
            a.set_animated(True)

        self.state = {"paused": False, "quit": False, "grab": False}
        self.bg = None
        self.dirty = False
        self.ylim = 0.0
        self.next_draw = 0.0
        self.hist_t, self.hist_c = [], []

        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("resize_event", self._invalidate)
        plt.show(block=False)

    def _on_key(self, ev):
        if ev.key == "p":
            self.state["paused"] = not self.state["paused"]
        elif ev.key == "q":
            self.state["quit"] = True
        elif ev.key == "s":
            self.state["grab"] = True

    def _invalidate(self, _ev=None):
        self.bg = None

    def alive(self):
        return plt.fignum_exists(self.fig.number)

    def idle(self, sleep=0.0):
        self.fig.canvas.flush_events()
        if sleep:
            time.sleep(sleep)

    def mark_sync(self, t):
        self.ax_hi.axvline(t, color="red", ls="--", lw=1.2)
        self.ax_hi.annotate("sync", (t, 1.02), xycoords=("data", "axes fraction"),
                            color="red", fontsize=8, ha="center")
        self.dirty = True

    def draw(self, now, label, sig, d, cross, spread, lag, tone, snr, fs, frames):
        args = self.args
        self.hist_t.append(now)
        self.hist_c.append(cross)
        if now < self.next_draw:
            self.idle()
            return
        self.next_draw = now + 1.0 / args.fps

        n = len(sig[0])
        n_show = n if args.cycles <= 0 else int(
            min(n, max(64, args.cycles * fs / tone)))
        i0 = min(trigger_index(sig[0]), n - n_show)
        # Agg costs time per pixel of path drawn, not per point, so a
        # decimated full-swing sine is far more expensive than its point
        # count suggests: 4096 points cost 671 ms here, 1024 cost 22 ms.
        step = max(1, n_show // 1000)
        idx = np.arange(i0, i0 + n_show, step)
        x_us = (idx - i0) / fs * 1e6
        for ln, s in zip(self.lines, sig):
            ln.set_data(x_us, s[idx])
        if abs(self.ax_tr.get_xlim()[1] - x_us[-1]) > 1e-9:
            self.ax_tr.set_xlim(0, x_us[-1])
            self.dirty = True
        peak = max(float(np.max(np.abs(s[idx]))) for s in sig)
        if peak > self.ylim * 0.98 or peak < self.ylim * 0.4:
            self.ylim = peak * 1.25
            self.ax_tr.set_ylim(-self.ylim, self.ylim)
            self.dirty = True

        self.hist_line.set_data(self.hist_t, self.hist_c)
        # The spec band is always in view, so a large offset makes the range
        # much taller than the data spread. Pad against the whole visible
        # range, otherwise a flat trace at +779 ns lands on the top spine.
        lo = min(min(self.hist_c), -SPEC_NS * 1.2)
        hi = max(max(self.hist_c), SPEC_NS * 1.2)
        pad = max(2.0, (hi - lo) * 0.08)
        want = (lo - pad, hi + pad)
        if max(abs(a - b) for a, b in zip(self.ax_hi.get_ylim(), want)) > 0.5:
            self.ax_hi.set_ylim(*want)
            self.dirty = True

        self.txt.set_text(
            f"[{label}]  t {now:7.1f} s   ODR {fs / 1e6:.4f} MSPS   "
            f"tone {tone:9.1f} Hz   SNR {snr:5.1f} dB   frames {frames}\n"
            f"cross (die B - die A) {cross:+8.1f} ns    "
            f"spread {spread:6.1f} ns    lag {lag:+d} samples\n"
            f"per-ch vs ch0: "
            + "  ".join(f"{v:+7.1f}" for v in d[:4]) + "   |   "
            + "  ".join(f"{v:+7.1f}" for v in d[4:8]))

        if self.dirty or self.bg is None:
            self.fig.canvas.draw()          # animated artists are skipped
            self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
            self.dirty = False
        self.fig.canvas.restore_region(self.bg)
        for ln in self.lines:
            self.ax_tr.draw_artist(ln)
        self.ax_hi.draw_artist(self.hist_line)
        self.fig.draw_artist(self.txt)
        self.fig.canvas.blit(self.fig.bbox)
        self.fig.canvas.flush_events()


# ----------------------------------------------------------------- reporting

def print_head(nch):
    cols = "".join(f"{f'ch{i}':>9}" for i in range(nch))
    print(f"\n  {'t_s':>7} {'cross':>9} {'spread':>8} {'lag':>5} "
          f"{'tone_Hz':>10} {'SNR':>6} |{cols}")
    print("  " + "-" * (49 + 9 * nch))


def print_row(t, cross, spread, lag, tone, snr, d):
    print(f"  {t:>7.1f} {cross:>+9.1f} {spread:>8.1f} {lag:>+5d} "
          f"{tone:>10.1f} {snr:>6.1f} |"
          + "".join(f"{v:>+9.1f}" for v in d))


def stats(label, cross, spreads, lags, frames, skipped, elapsed, files, why):
    c = np.array(cross) if cross else np.array([np.nan])
    s = np.array([v for v in spreads if not np.isnan(v)])
    return {
        "label": label, "n": len(cross), "frames": frames, "skipped": skipped,
        "elapsed": elapsed, "files": files, "why": why,
        "mean": float(np.mean(c)), "std": float(np.std(c)),
        "min": float(np.min(c)), "max": float(np.max(c)),
        "span": float(np.ptp(c)),
        "spread": float(np.mean(s)) if len(s) else float("nan"),
        "lag_min": int(min(lags)) if lags else 0,
        "lag_max": int(max(lags)) if lags else 0,
    }


def print_phase(st):
    print(f"\n{'=' * 72}\n  {st['label']} phase")
    print(f"{'=' * 72}")
    print(f"  frames        : {st['frames']} refills in {st['elapsed']:.1f} s "
          f"({st['frames'] / max(st['elapsed'], 1e-9):.1f}/s), "
          f"{st['skipped']} skipped on low SNR")
    print(f"  ended         : {st['why']}")
    print(f"  cross         : mean {st['mean']:+.2f}  std {st['std']:.2f}  "
          f"min {st['min']:+.2f}  max {st['max']:+.2f}  span {st['span']:.2f} ns")
    print(f"  intra-die spread: mean {st['spread']:.2f} ns")
    print(f"  coarse lag    : min {st['lag_min']:+d}  max {st['lag_max']:+d} samples")
    v = "WITHIN" if abs(st["mean"]) <= SPEC_NS else "OUTSIDE"
    print(f"  verdict       : {v} the +/-{SPEC_NS:.0f} ns device-to-device spec")
    for f in st["files"]:
        print(f"  file          : {f}")
    print("=" * 72)


def print_compare(a, b):
    print(f"\n{'=' * 72}\n  BEFORE vs AFTER sync")
    print(f"{'=' * 72}")
    print(f"  {'metric':<22}{'before':>14}{'after':>14}{'change':>14}")
    print("  " + "-" * 62)
    for key, name in (("mean", "cross mean (ns)"),
                      ("std", "cross std (ns)"),
                      ("span", "cross span (ns)"),
                      ("spread", "intra-die spread (ns)")):
        va, vb = a[key], b[key]
        print(f"  {name:<22}{va:>14.2f}{vb:>14.2f}{vb - va:>+14.2f}")
    lag_a = f"{a['lag_min']:+d}..{a['lag_max']:+d}"
    lag_b = f"{b['lag_min']:+d}..{b['lag_max']:+d}"
    print(f"  {'coarse lag range':<22}{lag_a:>14}{lag_b:>14}")
    print("  " + "-" * 62)
    print(f"\n  sync moved the mean offset {a['mean']:+.2f} -> {b['mean']:+.2f} ns "
          f"({b['mean'] - a['mean']:+.2f} ns)")
    va = "WITHIN" if abs(a["mean"]) <= SPEC_NS else "OUTSIDE"
    vb = "WITHIN" if abs(b["mean"]) <= SPEC_NS else "OUTSIDE"
    print(f"  before: {va} spec        after: {vb} spec")
    for st in (a, b):
        if "CUT SHORT" in st["why"]:
            print(f"  WARNING: the {st['label']} phase {st['why']} - the two "
                  "phases are not equal-length, compare with care")
    print("=" * 72)


# ----------------------------------------------------------------- phase loop

def run_phase(label, src, scope, args, fs, t_global0, prefix):
    """Capture for args.minutes, printing a delay row every --interval seconds
    and dumping one --window buffer of raw every --grab-every seconds."""
    duration = args.minutes * 60.0
    meas = MeasLog(f"{prefix}_phase.csv", 8)
    files = [meas.path]
    cross_l, spreads, lags = [], [], []
    frames = skipped = grabs = 0
    grouped = None
    t_start = time.time()
    next_print = 0.0
    next_grab = args.grab_every if args.grab_every > 0 else float("inf")

    print(f"\n{'-' * 72}\n  {label} phase: {args.minutes:g} min "
          f"({duration:.0f} s)\n{'-' * 72}")
    print_head(8)

    why = None
    while True:
        now = time.time() - t_start
        if now >= duration:
            why = f"reached the full {args.minutes:g} min"
            break
        if scope.state["quit"]:
            why = f"CUT SHORT at {now:.1f} s - 'q' pressed"
            break
        if not scope.alive():
            scope.state["quit"] = True
            why = f"CUT SHORT at {now:.1f} s - plot window was closed"
            break
        if scope.state["paused"]:
            scope.idle(0.05)
            continue

        due = scope.state["grab"] or now >= next_grab
        if due:
            keyed = scope.state["grab"]
            scope.state["grab"] = False
            if now >= next_grab:
                next_grab += args.grab_every
            files.append(do_grab(src, args.window, fs,
                                 f"{prefix}_raw_{grabs:03d}.csv",
                                 "'s' pressed" if keyed else "periodic grab"))
            grabs += 1
            continue

        sig = src.read()
        frames += 1
        d, tone, snr, amps = cross_delays_ns(sig, fs)
        if d is None or snr < args.min_snr:
            skipped += 1
            scope.idle()
            continue

        if grouped is None:
            quiet = [i for i, a in enumerate(amps) if a < 0.05 * amps[0]]
            grouped = len(amps) >= 8 and not quiet
            if quiet:
                print(f"  NOTE: no tone on channel(s) {quiet}")

        if grouped:
            cross = float(np.mean(d[4:8]) - np.mean(d[0:4]))
            spread = float(max(np.ptp(d[0:4]), np.ptp(d[4:8])))
        else:
            cross = float(d[4] - d[0]) if len(d) > 4 else float("nan")
            spread = float("nan")
        lag = coarse_lag(sig[0], sig[4]) if len(sig) > 4 else 0

        cross_l.append(cross)
        spreads.append(spread)
        lags.append(lag)
        meas.row(now, cross, spread, lag, tone, snr, d)

        if now >= next_print:
            next_print = now + args.interval
            print_row(now, cross, spread, lag, tone, snr, d)

        scope.draw(time.time() - t_global0, label, sig, d, cross, spread, lag,
                   tone, snr, fs, frames)

    meas.close()
    # An 's' pressed in the last moments of a phase would otherwise fire on the
    # first frame of the next one and be filed under the wrong label.
    scope.state["grab"] = False
    print(f"  wrote {meas.path} ({meas.rows} rows)")
    return stats(label, cross_l, spreads, lags, frames, skipped,
                 time.time() - t_start, files, why)


# ----------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(
        description="Live 8-channel raw display, before/after multidevice sync.")
    p.add_argument("uri", nargs="?", help="e.g. ip:10.48.65.200 (omit with --demo)")
    p.add_argument("--minutes", type=float, default=5.0,
                   help="duration of EACH capture phase (default 5)")
    p.add_argument("--sync-compare", action="store_true",
                   help="run --minutes, issue DIG_IF_RESET once, run --minutes again")
    p.add_argument("--sync", action="store_true",
                   help="single-phase mode: sync once before starting")
    p.add_argument("--odr", type=int, help="set sampling_frequency before the run")
    p.add_argument("--interval", type=float, default=10.0,
                   help="seconds between printed delay rows (default 10)")
    p.add_argument("--grab-every", type=float, default=0.0,
                   help="also dump raw every N seconds during a phase; "
                        "0 (default) = only around the sync and on the 's' key")
    p.add_argument("--outdir", default=".",
                   help="parent of the per-run ad7134_<stamp>/ folder "
                        "(default: the current directory)")
    p.add_argument("--window", type=int, default=65536,
                   help="buffer size in samples: both the refill size and the "
                        "length of every raw dump. Default 65536 = 4.3 MB per "
                        "dump. Keep it a power of two - the 65534 the other "
                        "scripts use factors as 2*7*31*151, which makes the "
                        "per-frame FFTs 3x slower. The DMAC caps a transfer at "
                        "16 MB = 524288 samples; a larger window also means "
                        "fewer refills per second, so a coarser history strip")
    p.add_argument("--fps", type=float, default=5.0, help="display refresh cap")
    p.add_argument("--cycles", type=float, default=3.0,
                   help="tone cycles shown in the trace panel; 0 = whole "
                        "buffer, which is decimated and therefore an aliased "
                        "amplitude overview, not a waveform (the phase "
                        "measurement always uses every sample)")
    p.add_argument("--crc", action="store_true", help="24-bit+CRC decode (shift=8)")
    p.add_argument("--min-snr", type=float, default=30.0,
                   help="freeze the phase readout below this SNR")
    p.add_argument("--demo", action="store_true", help="synthetic source, no hardware")
    p.add_argument("--demo-delay-ns", type=float, default=8.0,
                   help="inter-die delay the demo source fakes before sync")
    p.add_argument("--demo-delay-after-ns", type=float, default=8.0,
                   help="inter-die delay the demo source fakes after sync")
    p.add_argument("--demo-tone", type=float, default=20000.0)
    args = p.parse_args()

    if not args.demo and not args.uri:
        p.error("a uri is required unless --demo is given")
    require_gui()

    # Every run gets its own folder, so back-to-back runs never mix and there is
    # nothing to remember on the command line. --outdir picks the parent.
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rundir = os.path.join(args.outdir, f"ad7134_{stamp}")
    os.makedirs(rundir, exist_ok=True)
    print(f"saving to {os.path.abspath(rundir)}/")

    if args.demo:
        src = DemoSource(args.window, float(args.odr) if args.odr else DEMO_FS,
                         args.demo_tone, args.demo_delay_ns,
                         args.demo_delay_after_ns)
    else:
        src = HwSource(args.uri, args.window, args.crc, args.odr)
    fs = src.fs

    n_phases = 2 if args.sync_compare else 1
    check_budget(rundir, args, fs, n_phases)

    total_s = n_phases * args.minutes * 60.0
    scope = Scope(total_s, args)
    t0 = time.time()

    print(f"\nrunning - [s] grab raw   [p] pause   [q] quit")
    results = []
    try:
        if args.sync_compare:
            src.status("BEFORE")
            results.append(run_phase("BEFORE", src, scope, args, fs, t0,
                                     f"{rundir}/before_sync"))
            if not scope.state["quit"] and scope.alive():
                # These two bracket the sync as tightly as the hardware allows:
                # the last buffer the unsynced pair produced, and the first one
                # the synced pair produces. Nothing runs in between except the
                # DIG_IF_RESET itself.
                results[-1]["files"].append(
                    do_grab(src, args.window, fs,
                            f"{rundir}/before_sync_raw.csv", "last buffer before sync"))
                print(f"\n  >> issuing DIG_IF_RESET broadcast\n")
                src.sync()
                scope.mark_sync(time.time() - t0)
                after_grab = do_grab(src, args.window, fs,
                                     f"{rundir}/after_sync_raw.csv",
                                     "first buffer after sync")
                results.append(run_phase("AFTER", src, scope, args, fs, t0,
                                         f"{rundir}/after_sync"))
                results[-1]["files"].insert(0, after_grab)
            else:
                print("\n  >> BEFORE phase ended early, so no sync was issued "
                      "and the AFTER phase was skipped")
            src.status("AFTER")
        else:
            src.status("BEFORE")
            if args.sync:
                src.sync()
            results.append(run_phase("RUN", src, scope, args, fs, t0, f"{rundir}/run"))
            src.status("AFTER")
    except KeyboardInterrupt:
        print("\ninterrupted")

    src.close()
    for st in results:
        print_phase(st)
    if len(results) == 2:
        print_compare(results[0], results[1])
    plt.close("all")


if __name__ == "__main__":
    main()
