#!/usr/bin/env python3
# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Long-run inter-chip drift monitor for the dual AD7134.

Measures, repeatedly over a long capture, the delay of every channel relative
to channel 0, and classifies the cross-chip pair as stable / linear drift /
staircase / thermal.

The intra-chip pair (ch0 vs ch1, same die, same clock) is measured at the same
time and used as a CONTROL: it cannot physically drift, so whatever it shows is
the noise floor of the stimulus + cabling + estimator. If the control drifts,
the setup is lying and the cross-chip number means nothing.

Run from the pyadi-iio root, like the other ad7134 examples. The board address
is DHCP-assigned, so substitute the current one.

Continuous capture (1.4 MHz ODR, 20 kHz / 2 Vpp / 0 V offset sine split to
ch0 and ch4) — the buffer is created once and held open for the whole run:

    python3 examples/ad7134_drift_monitor.py ip:<board> \
        --odr 1400000 --sync --minutes 60 --csv drift_1400k.csv

Burst capture — --rearm destroys and recreates the buffer around every
measurement, which gates the SPI Engine offload trigger off between bursts.
--window sizes each burst; it does NOT by itself create burst mode:

    python3 examples/ad7134_drift_monitor.py ip:<board> \
        --odr 1400000 --sync --minutes 20 --window 2097152 --interval 0.5 \
        --rearm --csv drift_burst.csv
"""

import argparse
import sys
import time

import numpy as np

try:
    import iio
except ImportError:
    sys.exit("python3 libiio bindings not found (apt install python3-libiio)")


# ------------------------------------------------------------------ raw decode

def decode(raw, fmt, shift=None):
    """Convert de-interleaved channel bytes to float64, honouring 16/24/32-bit
    storage (the -24 DTS variant uses 24-bit storagebits = 3 bytes/sample).

    @shift overrides fmt.shift. Needed in 24-bit+CRC mode: the driver hardcodes
    storagebits=32 shift=0 for every frame format (ad4134.c:212-213), so the
    CRC and non-CRC scan types are indistinguishable, but the CRC word is
    data[31:8] + header[7:0] and needs shift=8."""
    if fmt.is_be:
        sys.exit("big-endian scan format not handled")
    nbytes = fmt.length // 8
    b = np.frombuffer(raw, dtype=np.uint8)
    b = b[: (len(b) // nbytes) * nbytes].reshape(-1, nbytes)
    v = np.zeros(len(b), dtype=np.int64)
    for i in range(nbytes):
        v |= b[:, i].astype(np.int64) << (8 * i)
    v >>= fmt.shift if shift is None else shift
    bits = fmt.bits
    v &= (1 << bits) - 1
    if fmt.is_signed:
        v = np.where(v >= (1 << (bits - 1)), v - (1 << bits), v)
    return v.astype(np.float64)


def headers(raw, fmt):
    """Low byte of each word: the AD7134 per-sample status/CRC header in
    24-bit+CRC mode. Bit 7 chip error, bit 6 filter settled + PLL locked,
    [5:0] CRC-6."""
    nbytes = fmt.length // 8
    b = np.frombuffer(raw, dtype=np.uint8)
    return b[: (len(b) // nbytes) * nbytes].reshape(-1, nbytes)[:, 0]


# ------------------------------------------------------------------ estimators

def cross_delays_ns(sig, fs):
    """Delay of every channel relative to sig[0], from the cross-spectrum phase
    at the dominant tone. Returns (delays_ns, tone_hz, snr_db)."""
    n = len(sig[0])
    w = np.hanning(n)
    spec = [np.fft.rfft((s - s.mean()) * w) for s in sig]

    mag = np.abs(spec[0])
    mag[0] = 0.0
    k = int(np.argmax(mag))
    if k < 1 or k >= len(mag) - 1:
        return None, None, None, None

    lm = np.log(mag[k - 1:k + 2] + 1e-30)
    denom = lm[0] - 2 * lm[1] + lm[2]
    delta = 0.5 * (lm[0] - lm[2]) / denom if denom != 0 else 0.0
    tone = (k + delta) * fs / n

    ref = spec[0][k]
    delays = [np.angle(ref * np.conj(S[k])) / (2 * np.pi * tone) * 1e9
              for S in spec]
    amps = np.array([np.abs(S[k]) for S in spec])

    noise = np.sqrt(np.mean(np.delete(mag, [k - 1, k, k + 1]) ** 2))
    snr = 20 * np.log10(mag[k] / (noise + 1e-30))
    return np.array(delays), tone, snr, amps


def coarse_lag(a, b):
    """Integer-sample lag via FFT cross-correlation - catches whole-sample slips
    that the phase estimate folds away."""
    n = len(a)
    A = np.fft.rfft(a - a.mean(), 2 * n)
    B = np.fft.rfft(b - b.mean(), 2 * n)
    c = np.fft.irfft(A * np.conj(B), 2 * n)
    c = np.concatenate((c[-n:], c[:n]))
    return int(np.argmax(c)) - n


def unwrap(series, period_ns):
    out = [series[0]]
    for v in series[1:]:
        out.append(v + round((out[-1] - v) / period_ns) * period_ns)
    return np.array(out)


# ----------------------------------------------------------------- device glue

def find_device(ctx):
    for dev in ctx.devices:
        chans = [c for c in dev.channels if not c.output and c.scan_element]
        if len(chans) >= 8:
            return dev, chans
    for dev in ctx.devices:
        chans = [c for c in dev.channels if not c.output and c.scan_element]
        if chans:
            return dev, chans
    sys.exit("no device with scan elements found")


def read_status(ctx):
    out = {}
    for dev in ctx.devices:
        if not dev.name or "adc" not in dev.name.lower():
            continue
        vals = {}
        for r in (0x15, 0x42):
            try:
                vals[r] = dev.reg_read(r)
            except OSError:
                vals[r] = None
        out[dev.name] = vals
    return out


def show_status(tag, status):
    print(f"\nchip registers {tag}:")
    for name, v in status.items():
        s, e = v.get(0x15), v.get(0x42)
        if s is None:
            line = "0x15=<unreadable>"
        elif s == 0xFF:
            line = "0x15=0xff  *** BUS FLOAT - chip not driving MISO, PLL bit is a FALSE POSITIVE ***"
        else:
            line = f"0x15=0x{s:02x} (PLL {'LOCKED' if s & 1 else 'UNLOCKED'})"
        if e is not None:
            flags = [n for bit, n in ((0x01, "ERR_MM_CRC"), (0x02, "ERR_ASRC"),
                                      (0x04, "ERR_FUSE_CRC"), (0x08, "ERR_DCLK"))
                     if e & bit]
            line += f"  0x42=0x{e:02x} [{','.join(flags) if flags else 'clean'}]"
        print(f"  {name}: {line}")


def trigger_sync(dev):
    """ad4134_sync is an IIO_SHARED_BY_ALL ext_info, so it lands in sysfs as
    'in_voltage_ad4134_sync' with no channel index. Depending on the libiio
    version that surfaces as a device attr or on an index-less channel, so
    search everywhere rather than assuming."""
    for name, attr in dev.attrs.items():
        if "sync" in name:
            attr.value = "1"
            print(f"sync triggered (device attr '{name}')")
            return True
    for c in dev.channels:
        for name, attr in c.attrs.items():
            if "sync" in name:
                attr.value = "1"
                print(f"sync triggered (channel '{c.id}' attr '{name}')")
                return True
    print("WARNING: no sync attribute found - continuing WITHOUT explicit sync.")
    print("         Drift slope is unaffected; only the starting offset is.")
    print(f"         device attrs: {sorted(dev.attrs)}")
    if dev.channels:
        print(f"         ch0 attrs:    {sorted(dev.channels[0].attrs)}")
    return False


# ------------------------------------------------------------------------ main

def main():
    p = argparse.ArgumentParser()
    p.add_argument("uri")
    p.add_argument("--odr", type=int, help="set sampling_frequency before the run")
    p.add_argument("--sync", action="store_true",
                   help="write ad4134_sync=1 after setting the ODR")
    p.add_argument("--minutes", type=float, default=60.0)
    p.add_argument("--window", type=int, default=16384)
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--min-snr", type=float, default=30.0,
                   help="reject captures below this SNR (dB); clean setup is ~75")
    p.add_argument("--pair", default="0,4", help="cross-chip pair (default 0,4)")
    p.add_argument("--control", default="0,1", help="intra-chip control pair")
    p.add_argument("--no-group", action="store_true",
                   help="force single-pair mode even if all 8 inputs are driven")
    p.add_argument("--spec", type=float, default=10.0,
                   help="inter-ADC skew spec in ns for the stability verdict")
    p.add_argument("--rearm", action="store_true",
                   help="destroy and recreate the capture buffer before every "
                        "measurement instead of holding one open, to emulate "
                        "iio-oscilloscope and test whether slips are triggered "
                        "by capture start rather than by elapsed time")
    p.add_argument("--drain", action="store_true",
                   help="hold ONE buffer open but refill it back-to-back so the "
                        "DMA ring never goes idle, analysing only every "
                        "--interval seconds. Holds the buffer open like a normal "
                        "run while removing the stall like --rearm, which is what "
                        "separates 'held-open buffer' from 'stalled DMA' as the "
                        "slip trigger. Use a large --interval so many refills are "
                        "discarded between measurements")
    p.add_argument("--crc", action="store_true",
                   help="board is running the 24-bit+CRC DTS variant, so every "
                        "32-bit word is data[31:8] + header[7:0]. The driver "
                        "reports the same scan_type either way (storagebits=32 "
                        "shift=0 hardcoded), so this cannot be auto-detected. "
                        "Decodes with shift=8 and reports the per-sample header: "
                        "bit7 chip error, bit6 filter settled + PLL locked")
    p.add_argument("--relative", action="store_true",
                   help="judge drift from the t=0 offset instead of from zero")
    p.add_argument("--csv")
    args = p.parse_args()

    ca, cb = (int(x) for x in args.pair.split(","))
    ka, kb = (int(x) for x in args.control.split(","))

    ctx = iio.Context(args.uri)
    dev, chans = find_device(ctx)
    print(f"device: {dev.name}  ({len(chans)} scan elements)")
    if len(chans) < 8:
        print("WARNING: not the 8-channel duo build. Two separate buffers CAN")
        print("         drift from host-side sample loss - different root cause.")

    if args.odr:
        dev.attrs["sampling_frequency"].value = str(args.odr)
        time.sleep(0.5)
    fs = float(dev.attrs["sampling_frequency"].value)
    print(f"sampling_frequency: {fs:.1f} Hz  ({1e9/fs:.2f} ns/sample)")

    synced = False
    if args.sync:
        synced = trigger_sync(dev)
        time.sleep(0.5)

    before = read_status(ctx)
    show_status("BEFORE", before)

    for c in chans:
        c.enabled = True
    def new_buffer():
        b = iio.Buffer(dev, args.window)
        if b is None:
            sys.exit("failed to create buffer")
        return b

    if args.rearm and args.drain:
        sys.exit("--rearm and --drain are mutually exclusive: one destroys the "
                 "buffer every measurement, the other holds it open for the run")

    buf = None if args.rearm else new_buffer()

    # ad7134_sync_demo.py:136-141 discards the first 3 captures after
    # DIG_IF_RESET. The frames already in the DMA ring when the reset lands
    # predate the alignment, so measuring them reports the pre-sync offset.
    if args.sync:
        fbuf = buf if buf is not None else new_buffer()
        for _ in range(3):
            fbuf.refill()
        if fbuf is not buf:
            # This pylibiio has no Buffer.destroy(); the DMA buffer is freed in
            # __del__, so the reference must be dropped or the next create
            # fails with EBUSY.
            if hasattr(fbuf, "destroy"):
                fbuf.destroy()
            fbuf = None
        print("\n" + "=" * 62)
        if synced:
            print("SYNCHRONIZATION DONE")
            print("  DIG_IF_RESET broadcast sent via the ad4134_sync attribute")
            print("  - the same action as writing ad4134_sync in iio-oscilloscope.")
            print("  Frame counters aligned, 3 captures discarded to flush the")
            print("  DMA ring of pre-reset frames. Measurements below are post-sync.")
        else:
            print("SYNCHRONIZATION NOT DONE")
            print("  No ad4134_sync attribute was found, so no DIG_IF_RESET was")
            print("  issued. The run continues, but it is NOT a synchronised run.")
        print("=" * 62)

    drained = 0
    if args.rearm:
        print("REARM MODE: buffer destroyed and recreated every measurement.")
        print("  Compare the slip rate against a normal run at identical")
        print("  settings. A higher rate here means the slip is triggered by")
        print("  capture start, not by elapsed time.")
    if args.drain:
        print("DRAIN MODE: one buffer held open, refilled back-to-back so the")
        print("  DMA ring never goes idle. Only every --interval seconds is")
        print("  analysed; the rest are discarded. Slips here mean the held-open")
        print("  buffer alone is the trigger and --rearm merely masked the fault.")
        print("  No slips mean the stall is required and --rearm is curative.")

    rows = []
    bad = 0
    control_ok = True
    grouped = False
    crc_reported = False
    t0 = time.time()
    deadline = t0 + args.minutes * 60.0
    next_at = t0

    print(f"\n{'t[s]':>8} {'cross[ns]':>11} {'ctrl[ns]':>10} {'spread':>9}"
          f" {'lag':>6} {'tone[Hz]':>10} {'SNR[dB]':>8}")
    try:
        while time.time() < deadline:
            now = time.time()
            if now < next_at:
                if args.drain:
                    buf.refill()
                    drained += 1
                else:
                    time.sleep(min(0.25, next_at - now))
                continue
            next_at += args.interval

            if args.rearm:
                buf = new_buffer()
            buf.refill()
            raws = [c.read(buf) for c in chans]
            sig = [decode(r, c.data_format, shift=8 if args.crc else None)
                   for r, c in zip(raws, chans)]
            if args.crc:
                hdr = [headers(r, c.data_format) for r, c in zip(raws, chans)]
                unsettled = [i for i, h in enumerate(hdr)
                             if not np.all(h & 0x40)]
                if unsettled:
                    frac = {i: float(np.mean((hdr[i] & 0x40) == 0))
                            for i in unsettled}
                    print(f"  HEADER bit6 LOW (filter unsettled / PLL unlocked) "
                          f"on ch {frac}")
                if not crc_reported:
                    crc_reported = True
                    err = {i: float(np.mean((h & 0x80) != 0))
                           for i, h in enumerate(hdr)}
                    print(f"  header bit7 (chip error) set fraction per ch: {err}")
            n = min(len(s) for s in sig)
            sig = [s[:n] for s in sig]
            if args.rearm:
                # Release the DMA buffer so the next iteration re-arms the
                # capture from scratch. Older pylibiio needs the explicit
                # destroy(); newer releases it on refcount drop.
                if hasattr(buf, "destroy"):
                    buf.destroy()
                buf = None

            d, tone, snr, amps = cross_delays_ns(sig, fs)
            if d is None:
                print("  (no tone found - is the generator connected?)")
                continue
            # A clean capture of this setup runs ~75 dB. Anything near the noise
            # floor means the buffer is being shared with another IIO client or
            # the ADC is not converting - such a row carries no phase info.
            if snr < args.min_snr:
                print(f"  SKIP: SNR {snr:.1f} dB < {args.min_snr:.0f} dB at"
                      f" {tone:.0f} Hz - capture is garbage, not measuring.")
                bad += 1
                if bad == 3:
                    print("  >>> 3 bad captures. Close iio-oscilloscope / any other"
                          " client holding the buffer, then restart.")
                continue
            if not rows:
                quiet = [i for i in range(len(amps)) if amps[i] < 0.05 * amps[ca]]
                if quiet:
                    print(f"  NOTE: no tone on channel(s) {quiet}.")
                    if ka in quiet or kb in quiet:
                        control_ok = False
                        print("  control pair DISABLED - run loses its validity check.")
                grouped = (len(amps) >= 8 and not quiet and not args.no_group)
                print("  all 8 channels driven -> using per-die 4-channel average"
                      if grouped else "  using single-channel pair")
            lag = coarse_lag(sig[ca], sig[cb])
            t = time.time() - t0
            # With all 8 inputs tied to one node, average the four channels of
            # each die: halves the estimator noise and makes a per-channel
            # glitch obvious as a jump in the intra-die spread.
            if grouped:
                cross_v = float(np.mean(d[4:8]) - np.mean(d[0:4]))
                spread = max(np.ptp(d[0:4]), np.ptp(d[4:8]))
            else:
                cross_v = float(d[cb] - d[ca])
                spread = float("nan")
            rows.append((t, cross_v, float(d[kb] - d[ka]), lag, tone, snr,
                         d.copy(), spread))
            print(f"{t:8.1f} {cross_v:11.1f} {rows[-1][2]:10.1f} {spread:9.1f}"
                  f" {lag:6d} {tone:10.1f} {snr:8.1f}")
    except KeyboardInterrupt:
        print("\ninterrupted")

    show_status("AFTER", read_status(ctx))

    if len(rows) < 5:
        sys.exit("\nnot enough measurements to judge drift")

    t = np.array([r[0] for r in rows])
    tone = float(np.median([r[4] for r in rows]))
    period_ns = 1e9 / tone
    cross = unwrap([r[1] for r in rows], period_ns)
    ctrl = unwrap([r[2] for r in rows], period_ns)
    lag = np.array([r[3] for r in rows])

    Ts = 1e9 / fs

    # A linear-fit residual is useless as a noise floor here: discrete slips
    # inflate it until they no longer clear their own detection threshold.
    # The MAD of successive differences ignores anything that is not a
    # sample-to-sample wiggle.
    def robust_noise(y):
        d = np.abs(np.diff(y))
        return max(1.4826 * float(np.median(d)) / 1.414, 1e-3)

    def fit(y):
        slope, icept = np.polyfit(t, y, 1)
        return slope, robust_noise(y), y.max() - y.min()

    s_x, n_x, span_x = fit(cross)
    s_c, n_c, span_c = fit(ctrl)

    # Decompose the cross series into whole-ODR-period frame slips and the
    # sub-period phase offset that survives them.
    kslip = np.round(cross / Ts).astype(int)
    fine = cross - kslip * Ts
    fine -= round(float(np.median(fine)) / Ts) * Ts
    jumps = [(i, kslip[i + 1] - kslip[i]) for i in range(len(kslip) - 1)
             if kslip[i + 1] != kslip[i]]

    label = "die A avg -> die B avg" if grouped else f"ch{ca}->ch{cb}"
    spread = np.array([r[7] for r in rows])

    print("\n" + "=" * 66)
    print(f"measurements  : {len(rows)} over {t[-1]/60:.1f} min")
    if args.drain:
        print(f"drained       : {drained} discarded refills "
              f"({(drained + len(rows)) / max(t[-1], 1e-9):.1f} refills/s, "
              f"ring kept busy)")
    print(f"tone          : {tone:.1f} Hz   (unambiguous +-{period_ns/2:.0f} ns)")
    if grouped:
        print(f"intra-die spread: mean {np.nanmean(spread):.2f}  max {np.nanmax(spread):.2f} ns"
              "  (channel skew within one die - must stay flat)")
    print(f"CROSS {label} : start {cross[0]:+.1f}  end {cross[-1]:+.1f}  span {span_x:.1f} ns")
    print(f"                slope {s_x:+.4f} ns/s = {s_x/1000:+.5f} ppm,  noise {n_x:.2f} ns")
    print(f"CTRL  ch{ka}->ch{kb} : start {ctrl[0]:+.1f}  end {ctrl[-1]:+.1f}  span {span_c:.1f} ns")
    print(f"                slope {s_c:+.4f} ns/s = {s_c/1000:+.5f} ppm,  noise {n_c:.2f} ns")
    print(f"coarse lag    : min {lag.min():+d}  max {lag.max():+d} samples"
          f"  ({(lag.max()-lag.min())*1e9/fs:.0f} ns whole-sample slip)")
    print(f"frame slips   : {len(jumps)} event(s), levels k={kslip.min():+d}..{kslip.max():+d}"
          f"  net {kslip[-1]-kslip[0]:+d} periods")
    print(f"fine offset   : mean {fine.mean():+.2f}  std {fine.std():.2f}  span {np.ptp(fine):.2f} ns"
          f"  (sub-period phase, survives the slips)")

    print("-" * 66)
    if control_ok and abs(s_c) > 0.3 * max(abs(s_x), 1e-9) and abs(s_c) > 0.05:
        print("INVALID: the intra-chip CONTROL pair drifts too. Two channels on the")
        print("  same die share a clock and cannot drift - so this is the stimulus,")
        print("  the cabling or the estimator. Fix the setup before trusting CROSS.")
        print("  Most likely cause: ch0 and ch4 fed from two different generator")
        print("  outputs instead of one output through a splitter.")
    elif len(jumps) > 0 and fine.std() < 0.05 * Ts:
        # fine.std() small => the sub-period phase is invariant, so the steps
        # are true slips. A linear ramp would smear fine across the period.
        rate = len(jumps) / (t[-1] / 3600.0)
        print(f"FRAME SLIP: {len(jumps)} whole-ODR-period slip(s) in {t[-1]/60:.1f} min"
              f"  ({rate:.1f}/hour)")
        for i, dk in jumps:
            print(f"    t={t[i+1]:7.1f}s  {dk:+d} period(s) = {dk*Ts:+.1f} ns"
                  f"   (k {kslip[i]:+d} -> {kslip[i+1]:+d})")
        hist = {}
        for _, dk in jumps:
            hist[dk] = hist.get(dk, 0) + 1
        print("    jump histogram: "
              + "  ".join(f"{k:+d}p x{v}" for k, v in sorted(hist.items())))
        if abs(kslip[-1] - kslip[0]) <= 1 and len(jumps) >= 3:
            print("  Zero-mean random walk: no restoring force, so the separation is")
            print("  unbounded over long runs - this is what a user reports as 'drift'.")
        print(f"  The fine offset stays at {fine.mean():+.1f} ns throughout, so the")
        print("  sub-sample phase alignment is intact; only the frame/sample index")
        print("  slips. Mechanism = ASRC re-pick or ODR/XTAL non-commensurability,")
        print("  NOT a clock-frequency difference (that would ramp, not step).")
    elif abs(s_x) * t[-1] > max(5 * n_x, 10.0):
        print(f"LINEAR DRIFT: {s_x:+.3f} ns/s ({s_x/1000:+.4f} ppm).")
        print("  The chips are not sharing a timebase. Check 0x15 on both, and")
        print("  confirm XTAL2_CLKIN reaches both chips in this bitstream.")
    elif span_x > max(10 * n_x, 20.0):
        print("BOUNDED WANDER: no linear term, no discrete steps - most likely")
        print("  thermal settling. Compare against time-since-power-on.")
    else:
        print(f"STABLE: no drift. Bound is {abs(s_x):.4f} ns/s"
              f" ({abs(s_x)/1000:.5f} ppm) over {t[-1]/60:.1f} min.")

    # The question this run exists to answer: once sync puts the two ADCs
    # inside spec, do they STAY there?
    off = np.abs(cross - cross[0]) if args.relative else np.abs(cross)
    inspec = off <= args.spec
    first_bad = np.argmin(inspec) if not inspec.all() else None
    worst = int(np.argmax(off))

    print("-" * 66)
    print(f"SYNC STABILITY  (spec |offset| <= {args.spec:.0f} ns"
          f"{', relative to t=0' if args.relative else ''})")
    print(f"  offset at t=0      : {cross[0] - (cross[0] if args.relative else 0):+.1f} ns")
    print(f"  worst offset       : {off[worst]:.1f} ns at t={t[worst]:.0f}s")
    print(f"  time in spec       : {inspec.sum()}/{len(inspec)} measurements"
          f"  ({100.0*inspec.mean():.1f} %)")
    if first_bad is None:
        print(f"  VERDICT: HOLDS - stayed inside {args.spec:.0f} ns for the whole"
              f" {t[-1]/60:.1f} min.")
    else:
        print(f"  first breach       : t={t[first_bad]:.0f}s"
              f"  ({t[first_bad]/60:.1f} min after sync), offset {off[first_bad]:.1f} ns")
        print(f"  VERDICT: BREAKS - sync does not survive. Alignment is achieved,")
        print("           then lost; nothing re-establishes it.")
    print("=" * 66)

    if args.csv:
        with open(args.csv, "w") as f:
            ncw = len(rows[0][6])
            f.write("t_s,cross_ns,ctrl_ns,intra_die_spread_ns,coarse_lag,tone_hz,snr_db,"
                    + ",".join(f"ch{i}_ns" for i in range(ncw)) + "\n")
            for r, cx, ct in zip(rows, cross, ctrl):
                f.write(f"{r[0]:.3f},{cx:.4f},{ct:.4f},{r[7]:.4f},{r[3]},"
                        f"{r[4]:.3f},{r[5]:.2f},"
                        + ",".join(f"{v:.4f}" for v in r[6]) + "\n")
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
