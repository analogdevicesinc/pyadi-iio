# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 LiDAR -- four-channel time-of-flight against an M2K-simulated echo.

The four-channel version of ada4356_lidar_example.py.  Everything downstream of
the M2K output connector is the acquisition chain you would ship; only the
propagation delay is synthetic:

  TDD ch0 -> trig_fmc_out -> M2K TI      "laser fires", a real FPGA-timed edge
  M2K W1  -> J11 -> all four front ends   echo, delayed by an array index
  TDD ch1..4 -> the four DMA syncs        capture gating, real
  threshold -> dt -> d = c*dt/2           range, real

Hardware:
  trig_fmc_out (FMC LA04_N) -> M2K TI
  M2K W1 -> J11 on the eval board, which fans out to all four inputs

Because J11 feeds every channel, this is one synthetic target measured four
times -- a timing-chain test, not four independent targets.  That is the point:
d = c*dt/2 turns 1 ns of inter-channel skew into 15 cm of range disagreement.
The echo edge is measured on all four channels in a single acquisition, so the
delays between them are read straight off the data -- no tone, no alignment
calibration, nothing between the measurement and the answer.

Usage:
  python3 ada4356_quad_lidar_example.py ip:192.168.0.106
  python3 ada4356_quad_lidar_example.py ip:192.168.0.106 --distance 50
  python3 ada4356_quad_lidar_example.py ip:192.168.0.106 --distance 50 --samples 16384
  python3 ada4356_quad_lidar_example.py ip:192.168.0.106 --gain 11k --filter fsel1
  python3 ada4356_quad_lidar_example.py ip:192.168.0.106 --echo sine --burst-us 100
"""

import argparse
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import adi

try:
    import libm2k
except ImportError:
    print("ERROR: libm2k is not installed; this example needs an M2K to make the echo")
    sys.exit(1)

SPEED_OF_LIGHT = 299792458.0
TDD_CLOCK_HZ = 125_000_000
TDD_CLOCK_PERIOD_NS = 1e9 / TDD_CLOCK_HZ  # 8 ns
M2K_SAMPLE_RATE = 75_000_000

CHANNEL_LABELS = ["A", "B", "C", "D"]
COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red"]

# The schematic, the DT hogs and the kernel commits all talk in GSEL pin levels
# while the IIO enum talks in transimpedance; print both so a capture can be
# matched against either vocabulary.
GSEL_CODE = {"133k": "00", "4k54": "01", "11k": "10"}

# The trigger edge and the DMA gate are driven from the same TDD clock, so
# opening the gate on the same cycle the laser fires puts t=0 of the flight
# at buffer sample 0 and the time-of-flight is just the sample index.
TRIG_ON_RAW = 1000
TRIG_WIDTH_RAW = 125  # 1 us
GATE_WIDTH_RAW = 100


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("uri", nargs="?", default="ip:192.168.0.106")
    ap.add_argument("--distance", type=float, default=50.0, help="target, metres")
    ap.add_argument("--samples", type=int, default=65536)
    # Long enough that the front end settles to a plateau.  At 200 ns it never
    # does, so "peak" is one noisy transient maximum and the half-peak crossing
    # inherits that noise; a flat top averages it over many samples.
    ap.add_argument("--pulse-ns", type=float, default=1000.0, help="echo pulse width")
    # Defaults are the measured working point at 11k with the 200R Howland
    # jumpers: 0.12 Vpp on +0.04 V, which lands near -3.6 dBFS.  The offset is
    # the dangerous one -- the pedestal is Q - TZ*I_dc, so at 200R a few tenths
    # of a volt of DC drives the TIA past its 10 uA linear input and it pins
    # flat against a rail.  At 2K jumpers both numbers go up ~10x.
    ap.add_argument("--amplitude", type=float, default=0.06, help="echo amplitude, V")
    ap.add_argument("--offset", type=float, default=0.04, help="M2K baseline, V")
    ap.add_argument("--gain", help="transimpedance, e.g. 11k")
    ap.add_argument("--echo", choices=("pulse", "sine"), default="pulse",
                    help="echo shape: rectangular step, or a tone burst")
    ap.add_argument("--burst-us", type=float, default=100.0,
                    help="tone burst length, us (--echo sine)")
    ap.add_argument("--burst-khz", type=float, default=100.0,
                    help="tone burst frequency, kHz (--echo sine)")
    ap.add_argument("--zoom-us", type=float, default=0.0,
                    help="width of the echo panel, us (0 = auto)")
    ap.add_argument("--filter", dest="filt", help="FREQ_SEL, fsel0 or fsel1")
    # Auto-detect is USB-only, which a WSL host cannot see without usbipd.
    ap.add_argument("--m2k-uri", default="", help="e.g. ip:192.168.2.1")
    # Four DMAs are armed from four Python threads. If the next frame lands
    # before they are all armed, some channels catch frame N and others N+1,
    # which reads as hundreds of samples of skew. The proven quad scripts use
    # 1 s for this reason; the single-channel LiDAR example can use a short
    # frame only because it has one DMA and no arming race.
    ap.add_argument("--frame-ms", type=float, default=1000.0, help="TDD frame")
    return ap.parse_args()


def configure_tdd(dev, frame_length, gate_on):
    """ch0 fires the laser, ch1..4 gate the four DMAs on the same cycle."""
    tdd = dev.tdd
    tdd.enable = False
    tdd.burst_count = 0
    tdd.frame_length_raw = frame_length

    tdd.channel[0].on_raw = TRIG_ON_RAW
    tdd.channel[0].off_raw = TRIG_ON_RAW + TRIG_WIDTH_RAW
    tdd.channel[0].enable = True

    for ch_idx in range(1, 5):
        tdd.channel[ch_idx].on_raw = gate_on
        tdd.channel[ch_idx].off_raw = gate_on + GATE_WIDTH_RAW
        tdd.channel[ch_idx].enable = True

    tdd.enable = True
    try:
        tdd.sync_soft = True
    except Exception:
        pass
    return tdd


def m2k_echo(aout, echo_delay_us, amplitude_v, offset_v, frame_us,
             kind="pulse", pulse_ns=1000.0, burst_us=100.0, burst_khz=100.0):
    """Flat baseline with the echo buried delay_samples in.

    "pulse" is a rectangular step: the fastest edge the front end can produce,
    so the best timing reference.  "sine" is the tone burst the single-channel
    example sends -- easier to see and open to FFT analysis, but its edge is an
    order of magnitude slower, so the arrival time is correspondingly noisier.
    """
    rate = aout.getSampleRate(0)
    n = int(frame_us * rate / 1e6)
    delay_samples = int(echo_delay_us * rate / 1e6)

    wave = np.full(n, offset_v)
    if kind == "sine":
        end = min(delay_samples + max(1, int(burst_us * rate / 1e6)), n)
        t = np.arange(end - delay_samples) / rate
        wave[delay_samples:end] = offset_v + amplitude_v * np.sin(
            2 * np.pi * burst_khz * 1e3 * t)
    else:
        end = min(delay_samples + max(1, int(pulse_ns * rate / 1e9)), n)
        wave[delay_samples:end] = offset_v + amplitude_v

    aout.setCyclic(True)
    aout.push(0, wave.tolist())
    return delay_samples / rate * 1e6, end - delay_samples


def find_edge(x, fs):
    """Sub-sample index of the echo's rising edge, at half of its peak.

    One sample is 8 ns = 1.2 m of range, so the linear interpolation between
    the two straddling samples is not a refinement -- without it every edge is
    quantised to 1.2 m and the four channels cannot be compared.
    """
    # The TIA inverts and parks near the top of the range.
    y = -(x.astype(np.float64) - np.median(x))

    peak = y.max()
    # MAD over the whole buffer.  A fixed leading window reports the echo's own
    # amplitude as "noise" whenever the echo lands inside it, which inflates the
    # detection threshold and wrecks the SNR column.
    noise = 1.4826 * np.median(np.abs(y - np.median(y)))
    if peak < 6.0 * max(noise, 1e-9):
        return None, peak, noise

    half = 0.5 * peak
    above = np.flatnonzero(y >= half)
    i = int(above[0])
    if i == 0:
        return float(i), peak, noise

    y0, y1 = y[i - 1], y[i]
    frac = (half - y0) / (y1 - y0) if y1 != y0 else 0.0
    return (i - 1) + float(frac), peak, noise


def spread_ns(edges, fs):
    v = np.array(list(edges.values()))
    return (v.max() - v.min()) / fs * 1e9 if v.size >= 2 else float("nan")


def report(title, data, fs):
    """Per-channel echo arrival, referenced to A.

    Absolute range is deliberately absent: it is only meaningful if the echo
    replays on the laser edge, and on firmware that cannot trigger the
    generator the echo lands wherever it likes.  The delay BETWEEN channels is
    unaffected -- all four see the same echo at the same instant.
    """
    print(f"\n=== {title} ===")
    print(f"{'Ch':>3}  {'edge (samp)':>12}  {'d vs A (ns)':>12}  {'d vs A (m)':>11}"
          f"  {'peak':>7}  {'SNR':>7}")

    rows = [(label, *find_edge(x, fs)) for label, x in zip(CHANNEL_LABELS, data)]
    edges = {label: e for label, e, _, _ in rows if e is not None}
    ref = edges.get("A")

    for label, edge, peak, noise in rows:
        if edge is None:
            print(f"{label:>3}  {'no echo':>12}  {'':>12}  {'':>11}"
                  f"  {peak:7.1f}  {peak / max(noise, 1e-9):7.1f}")
            continue
        d_ns = (edge - ref) / fs * 1e9 if ref is not None else float("nan")
        print(f"{label:>3}  {edge:12.3f}  {d_ns:12.2f}  "
              f"{d_ns * 1e-9 * SPEED_OF_LIGHT / 2:11.3f}"
              f"  {peak:7.1f}  {peak / max(noise, 1e-9):7.1f}")

    if len(edges) >= 2:
        ns = spread_ns(edges, fs)
        print(f"\n  inter-channel spread : {ns:.2f} ns "
              f"({ns * 1e-9 * SPEED_OF_LIGHT / 2:.3f} m)")
    return edges


PREFLIGHT_PNG = "/tmp/ada4356_quad_lidar_preflight.png"
LIDAR_PNG = "/tmp/ada4356_quad_lidar.png"


def plot_preflight(probe, fs, path=PREFLIGHT_PNG):
    """Draw the whole capture against the full ADC span.

    Min/max envelope rather than decimation, or a 25-sample echo falls between
    the plotted points and the picture looks like a flat DC line.  Fixed
    -8192..8191 axis on purpose: autoscaling a railed waveform makes it look
    like a healthy signal.
    """
    n = probe[0].size
    step = max(1, n // 2000)
    nbins = n // step
    t_us = (np.arange(nbins) * step) / fs * 1e6

    fig, ax = plt.subplots(figsize=(12, 5))
    for label, color, x in zip(CHANNEL_LABELS, COLORS, probe):
        v = np.asarray(x)[: nbins * step].reshape(nbins, step)
        ax.fill_between(t_us, v.min(axis=1), v.max(axis=1), color=color,
                        alpha=0.55, lw=0, label=label)
    ax.axhline(8191, color="k", ls=":", lw=0.9)
    ax.axhline(-8192, color="k", ls=":", lw=0.9, label="ADC rails")
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_ylim(-8800, 8800)
    ax.set_xlabel("time since gate open (us)")
    ax.set_ylabel("ADC codes")
    ax.set_title("Level check -- whole capture, full ADC span")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8, ncol=5)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def plot_lidar(data, fs, edges, frame_us, zoom_us=10.0, path=LIDAR_PNG):
    """Laser fires -> flight time -> echo arrives, in three panels.

    The laser edge is never in the captured data (it goes to the M2K, not an
    ADC input), so panel 1 is where it lives: the DMA gate opens on the same
    TDD cycle as the trigger, which is what makes capture sample 0 equal t=0.
    """
    n = data[0].size
    t_us = np.arange(n) / fs * 1e6
    inv = [-(np.asarray(x) - np.median(x)) for x in data]

    trig_us = TRIG_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    trig_w = TRIG_WIDTH_RAW * TDD_CLOCK_PERIOD_NS / 1000
    gate_w = GATE_WIDTH_RAW * TDD_CLOCK_PERIOD_NS / 1000

    fig = plt.figure(figsize=(13, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.3, 2.0], hspace=0.55)

    # --- panel 1: TDD timing around the trigger -----------------------
    ax = fig.add_subplot(gs[0])
    end = trig_us + max(4 * trig_w, 8.0)
    ax.plot([0, 0, end], [2, 2.7, 2.7], color="tab:green", lw=2)
    ax.plot([0, trig_us, trig_us, trig_us + trig_w, trig_us + trig_w, end],
            [1, 1, 1.7, 1.7, 1, 1], color="tab:orange", lw=2)
    ax.plot([0, trig_us, trig_us, trig_us + gate_w, trig_us + gate_w, end],
            [0, 0, 0.7, 0.7, 0, 0], color="tab:purple", lw=2)
    for y, label, color in ((2.35, "Frame", "tab:green"),
                            (1.35, "Laser trigger ch0 -> M2K TI", "tab:orange"),
                            (0.35, "DMA gate ch1..4", "tab:purple")):
        ax.text(-0.03 * end, y, label, ha="right", va="center",
                fontsize=8, fontweight="bold", color=color)
    ax.axvline(trig_us, color="k", ls=":", lw=0.9)
    ax.text(end, 3.75,
            "the gate opens on the same cycle as the trigger,\n"
            "so capture sample 0 is t=0 of the flight",
            fontsize=8, va="top", ha="right")
    ax.set_xlim(-0.55 * end, end)
    ax.set_ylim(-0.4, 3.9)
    ax.set_yticks([])
    ax.set_xlabel("time from frame start (us)", fontsize=9)
    ax.set_title(f"TDD timing -- frame {frame_us / 1000:.1f} ms",
                 fontsize=10, fontweight="bold")
    for s in ("left", "top", "right"):
        ax.spines[s].set_visible(False)

    # --- panel 2: the whole capture -----------------------------------
    ax = fig.add_subplot(gs[1])
    step = max(1, n // 2000)
    nb = n // step
    tb = (np.arange(nb) * step) / fs * 1e6
    for label, color, y in zip(CHANNEL_LABELS, COLORS, inv):
        v = y[: nb * step].reshape(nb, step)
        ax.fill_between(tb, v.min(axis=1), v.max(axis=1), color=color,
                        alpha=0.55, lw=0, label=label)
    ylo, yhi = ax.get_ylim()

    # The frame opens trig_us before the gate does, so it is outside the
    # captured data; drawn anyway, because "when did the frame start" is the
    # question this panel gets asked.
    ax.set_xlim(-1.6 * trig_us, t_us[-1] * 1.02)
    ax.axvline(-trig_us, color="tab:green", lw=2)
    ax.text(-trig_us, ylo * 0.75, " frame\n starts", color="tab:green",
            fontsize=8, fontweight="bold", va="bottom")
    ax.axvline(0, color="tab:orange", lw=2)
    ax.text(t_us[-1] * 0.012, yhi * 0.95,
            "laser fires (TDD ch0)\nDMA gate opens -> t=0",
            color="tab:orange", fontsize=8, fontweight="bold", va="top")

    if edges:
        a_us = float(np.mean(list(edges.values()))) / fs * 1e6
        ax.axvline(a_us, color="tab:red", lw=1.5)
        ax.annotate("", xy=(a_us, yhi * 0.42), xytext=(0, yhi * 0.42),
                    arrowprops=dict(arrowstyle="<->", color="tab:red", lw=1.3))
        ax.text(a_us / 2, yhi * 0.46, f"time of flight {a_us:.2f} us",
                color="tab:red", fontsize=8, fontweight="bold", ha="center")
        ax.text(a_us, yhi * 0.22, " echo returns", color="tab:red",
                fontsize=8, fontweight="bold", va="top")

    ax.set_xlabel("time since the laser fired (us)", fontsize=9)
    ax.set_ylabel("codes (inverted)", fontsize=9)
    ax.set_title(f"Full capture -- {n:,} samples ({t_us[-1]:.0f} us)",
                 fontsize=10, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8, ncol=5)

    # --- panel 3: the echo itself, plus a zoom on the crossings -------
    gs3 = gs[2].subgridspec(1, 2, width_ratios=[2, 1], wspace=0.18)
    ax = fig.add_subplot(gs3[0])
    if edges:
        a = float(np.mean(list(edges.values())))
        lo = max(0, int(a - 0.2 * zoom_us * fs / 1e6))
        hi = min(n, int(a + 0.8 * zoom_us * fs / 1e6))
    else:
        a, lo, hi = 0.0, 0, min(n, 4000)
    for label, color, y in zip(CHANNEL_LABELS, COLORS, inv):
        ax.plot(t_us[lo:hi], y[lo:hi], color=color, lw=1.1, label=label)
    for (label, e), color in zip(edges.items(), COLORS):
        ax.axvline(e / fs * 1e6, color=color, ls="--", lw=0.9)
    ax.set_xlabel("time since the laser fired (us)", fontsize=9)
    ax.set_ylabel("codes (inverted)", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
    if edges:
        ax.set_title(
            f"Echo detail -- arrival {a / fs * 1e6:.3f} us after the trigger\n"
            f"(NOT a range: the generator free-runs)",
            fontsize=10, fontweight="bold")

    axz = fig.add_subplot(gs3[1])
    if edges:
        ns = spread_ns(edges, fs)
        # Wide enough to hold the spread, never so wide that 8 ns of skew
        # collapses into the line width.
        w_us = max(0.06, 3.0 * ns / 1000.0)
        a_us = a / fs * 1e6
        z0 = max(0, int((a_us - w_us) * fs / 1e6))
        z1 = min(n, int((a_us + w_us) * fs / 1e6))
        for label, color, y in zip(CHANNEL_LABELS, COLORS, inv):
            axz.plot(t_us[z0:z1], y[z0:z1], color=color, lw=1.2,
                     marker=".", ms=4)
        ref = edges.get("A", min(edges.values()))
        for (label, e), color in zip(edges.items(), COLORS):
            axz.axvline(e / fs * 1e6, color=color, ls="--", lw=1.0)
        lines = "   ".join(
            f"{k} {(v - ref) / fs * 1e9:+.2f}" for k, v in edges.items()
        )
        axz.set_title(f"edge crossings, ns vs A\n{lines}\nspread {ns:.2f} ns = "
                      f"{ns * 1e-9 * SPEED_OF_LIGHT / 2:.3f} m",
                      fontsize=9, fontweight="bold")
    axz.set_xlabel("time since the laser fired (us)", fontsize=9)
    axz.grid(alpha=0.3)

    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def level_check(data, amplitude_v, offset_v, fs):
    """Reject a capture whose levels make the edge timing meaningless.

    The echo is a flat baseline plus a short pulse, so the symmetry test that
    suits a sine does not apply here; what matters is that no channel touches a
    rail and the TIA is not pinned by DC.
    """
    print(f"{'Ch':>3}  {'pedestal':>9}  {'min':>7}  {'max':>7}  {'pulse':>8}")
    clipped = 0
    for label, x in zip(CHANNEL_LABELS, data):
        lo, hi = float(x.min()), float(x.max())
        base = float(np.median(x))
        # The TIA inverts, so the echo drives codes down from the baseline.
        print(f"{label:>3}  {base:9.1f}  {lo:7.0f}  {hi:7.0f}  {base - lo:8.1f}")
        if hi >= 8150 or lo <= -8150:
            clipped += 1

    pedestal = float(np.mean([np.median(x) for x in data]))
    plot_preflight(data, fs)

    if clipped:
        print(f"\n  {clipped} channel(s) against the ADC rails -- lower "
              f"--amplitude (now {amplitude_v:.3f} V).")
        return False
    if pedestal < -1000:
        print(f"\n  Pedestal {pedestal:.0f} codes, expected positive. It is"
              f"\n  Q - TZ*I_dc, so a negative one means too much DC current:"
              f"\n  lower --offset (now {offset_v:.3f} V), roughly in proportion.")
        return False
    return True


def main():
    args = parse_args()

    echo_delay_us = (2 * args.distance / SPEED_OF_LIGHT) * 1e6
    print(f"Target {args.distance:.1f} m -> echo delay {echo_delay_us:.3f} us "
          f"({echo_delay_us * 1000 / TDD_CLOCK_PERIOD_NS:.1f} ADC samples)")

    dev = adi.ada4356_quad(uri=args.uri)
    if args.gain:
        dev.gain_mode = args.gain
    if args.filt:
        dev.filter_mode = args.filt
    dev.rx_buffer_size = args.samples
    fs = dev.sampling_frequency

    tz = dev.gain_mode
    filt = dev.filter_mode
    codes = {GSEL_CODE.get(v, "??") for v in tz.values()}
    gsel = f"   GSEL1:GSEL0 = {codes.pop()}" if len(codes) == 1 else ""
    print("Transimpedance     : "
          + "  ".join(f"{k} {v}" for k, v in tz.items()) + gsel)
    print("Front-end filter   : " + "  ".join(f"{k} {v}" for k, v in filt.items()))
    print(f"M2K drive          : {args.amplitude * 2:.3f} Vpp on "
          f"{args.offset:+.3f} V  -> W1 swings "
          f"{args.offset - args.amplitude:+.3f} .. {args.offset + args.amplitude:+.3f} V")
    frame_length = max(
        int(args.frame_ms * 1e-3 * TDD_CLOCK_HZ), TRIG_ON_RAW + args.samples + 2000
    )
    tdd = configure_tdd(dev, frame_length, gate_on=TRIG_ON_RAW)
    frame_us = frame_length * TDD_CLOCK_PERIOD_NS / 1000
    # The M2K replays on each trigger, so its buffer only has to cover the
    # capture, not the whole frame -- a 1 s frame would be 75 Msamples.
    capture_us = args.samples / TDD_CLOCK_HZ * 1e6 * 1.1
    print(f"TDD frame {frame_us:.1f} us, trigger at cycle {TRIG_ON_RAW}, "
          f"gate on the same cycle so sample 0 is t=0")

    m2k = libm2k.m2kOpen(args.m2k_uri) if args.m2k_uri else libm2k.m2kOpen()
    if not m2k:
        print("ERROR: M2K not found"
              + (f" at {args.m2k_uri}" if args.m2k_uri else " (USB auto-detect)"))
        return 1

    try:
        # calibrateDAC() measures W1 with the M2K's own ADC, so the ADC has to
        # be calibrated first or the DAC offset it computes is meaningless.
        # Worth being strict about here: at 200R Howland jumpers a few tenths of
        # a volt of DC error is enough on its own to rail the TIA.
        m2k.calibrateADC()
        m2k.calibrateDAC()
        aout = m2k.getAnalogOut()
        aout.setSampleRate(0, M2K_SAMPLE_RATE)
        aout.enableChannel(0, True)
        trig = aout.getTrigger()
        try:
            fw = m2k.getFirmwareVersion()
        except Exception:
            fw = "unknown"
        print(f"M2K firmware       : {fw}")

        # setAnalogOutTriggerSource() is rejected by this M2K's firmware
        # ("not configurable on the current board"), so the generator cannot be
        # hardware-triggered here and the echo replays free-running.  These are
        # the calls the working single-channel and ZCU102 scripts use.
        trig.setAnalogSource(libm2k.TRIGGER_TI)
        trig.setAnalogCondition(0, libm2k.RISING_EDGE_ANALOG)
        trig.setAnalogDelay(0)

        actual_delay_us, echo_samples = m2k_echo(
            aout, echo_delay_us, args.amplitude, args.offset, capture_us,
            kind=args.echo, pulse_ns=args.pulse_ns,
            burst_us=args.burst_us, burst_khz=args.burst_khz
        )
        shape = (f"{args.burst_khz:.0f} kHz burst, {args.burst_us:.0f} us"
                 if args.echo == "sine" else f"{args.pulse_ns:.0f} ns pulse")
        print(f"\nM2K echo at {actual_delay_us:.3f} us -- {shape} "
              f"({echo_samples} samples at {M2K_SAMPLE_RATE / 1e6:.0f} MSPS)")
        time.sleep(0.3)

        data = [x.astype(np.float64) for x in dev.rx()]
    finally:
        try:
            aout.stop()
        except Exception:
            pass
        libm2k.contextClose(m2k)

    ok = level_check(data, args.amplitude, args.offset, fs)

    # --amplitude 0 leaves a flat baseline, which is the DC probe used to find
    # where the pedestal sits with no drive.
    if args.amplitude == 0:
        print("\n  No drive commanded, so this is a DC probe: the pedestals above"
              "\n  are what the front end does with no echo. With J11 at 0 V they"
              "\n  should read ~+6750 (Q, the zero-current quiescent).")
        print(f"\nPlot saved: {PREFLIGHT_PNG}")
        return 0

    if not ok:
        print(f"\nPlot saved: {PREFLIGHT_PNG}")
        return 1

    edges = report("Echo arrival", data, fs)

    print("\n  No absolute range is reported. The echo only encodes time of"
          "\n  flight if the generator replays on the laser edge; where it"
          "\n  free-runs it sits at an arbitrary index that changes every run."
          "\n  The delays BETWEEN channels are unaffected -- all four see the"
          "\n  same echo at the same instant -- and are what this measures.")

    zoom = args.zoom_us or (args.burst_us * 1.5 if args.echo == "sine" else 10.0)
    plot_lidar(data, fs, edges, frame_us, zoom_us=zoom)
    print(f"\nPlot saved: {PREFLIGHT_PNG}")
    print(f"Plot saved: {LIDAR_PNG}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
