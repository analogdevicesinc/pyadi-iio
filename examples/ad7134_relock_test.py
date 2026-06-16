# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 within-boot ASRC re-lock test.
#
# Question this answers:
#   Is the inter-chip ±1-XTAL-cycle rung set ONCE at the §E RC->crystal
#   handover (fixed for the whole boot), or is it re-rolled every time the
#   ASRC/PLL re-locks?
#
# Why it matters:
#   - If the rung is FIXED for the boot regardless of how many re-locks we
#     do -> the latch is set at the §E handover clock-mux (hypothesis A').
#     The fix lives in the clkin_aligner HDL (handover retry).
#   - If the rung CHANGES from one re-lock to the next -> the latch is set
#     at the ASRC/PLL lock, downstream of §E (hypothesis B).  This also
#     explains why the probe-order / both-reset §E A/B came back null.
#     The fix is detect-and-retry the lock, or MPC_CONFIG fine-trim.
#
# What it does (NO reboot — §E handover is fixed for this boot):
#   For each iteration, force a fresh >500 SPS ASRC re-lock by dropping the
#   ODR to fs_low, settling, then jumping to fs_high; then DIG_IF_RESET and
#   measure the inter-chip delay (the rung).  Repeat N times in one boot.
#
#   The IIO handle is recreated each iteration because the AD7134 driver
#   returns EBUSY when sampling_frequency is written while a buffer is
#   attached.  Recreating the handle does NOT reset the chip — §E handover
#   state persists; only the ODR (PWM) changes, which is what re-locks the
#   ASRC/PLL in hardware.
#
# Control mode (--digonly): skip the ODR jump and only re-issue DIG_IF_RESET
#   each iteration.  Per the known behaviour (DIG_IF_RESET only resets the
#   frame counter, it does not re-lock), the rung should NOT move in this
#   mode — it isolates the ODR re-lock as the manipulation that matters.
#
# Usage:
#   python ad7134_relock_test.py <uri> [n_iter] [fs_high] [fs_low] [--digonly]
#
# Examples:
#   python ad7134_relock_test.py ip:10.48.65.161 20
#   python ad7134_relock_test.py ip:10.48.65.161 20 1400000 100000
#   python ad7134_relock_test.py ip:10.48.65.161 20 --digonly
#
# Requirements:
#   - iiod running on the target, both chips probed (adc_0 + adc_1)
#   - A common tone fed into chip A ch0 and chip B ch4 (low freq, ~20 kHz,
#     for the most accurate ns reading) — same setup as ad7134_reboot_test.py

import gc
import sys
import time

import numpy as np

import adi


def compute_phase_delay(x, y, Fs):
    """Return (f0, phase_deg, delay_ns) between signals x and y."""
    x = x - np.mean(x)
    y = y - np.mean(y)
    N = len(x)
    w = np.hanning(N)
    X = np.fft.fft(x * w)
    Y = np.fft.fft(y * w)
    f = np.arange(N) * (Fs / N)
    kpk = 1 + np.argmax(np.abs(X[1 : N // 2]))
    f0 = f[kpk]
    phi = np.angle(Y[kpk]) - np.angle(X[kpk])
    phi = np.arctan2(np.sin(phi), np.cos(phi))
    phase_deg = np.degrees(phi)
    delay_ns = -phi / (2 * np.pi * f0) * 1e9
    return f0, phase_deg, delay_ns


def measure_delays(dev, ch_a, ch_b, Fs, n_captures, label):
    """Capture n_captures frames and return list of delays in ns."""
    delays = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)
        f0, phase_deg, delay_ns = compute_phase_delay(x, y, Fs)
        delays.append(delay_ns)
        print(f"    [{label} {i + 1}]  f0={f0:.1f} Hz  phase={phase_deg:+.3f} deg  delay={delay_ns:+.1f} ns")
    return delays


def make_dev(uri, buffer_size, fs=None):
    """Create and configure a fresh ad7134 handle.  Returns (dev, Fs)."""
    dev = adi.ad7134(uri=uri)
    dev.rx_enabled_channels = list(range(8))
    dev.rx_buffer_size = buffer_size
    if fs is not None:
        dev.sampling_frequency = fs
    return dev, float(dev.sampling_frequency)


def teardown(dev):
    """Fully release a handle and its kernel buffer before a rate change."""
    try:
        dev.rx_destroy_buffer()
    except Exception:
        pass
    del dev
    gc.collect()
    time.sleep(0.3)


def relock(old_dev, uri, buffer_size, fs_low, fs_high, settle):
    """Force a fresh >500 SPS ASRC re-lock on a clean handle.

    Recreating the handle guarantees no active buffer exists when we write
    sampling_frequency (the driver returns EBUSY otherwise).  The chip is
    NOT reset; only the ODR (PWM) changes, which re-locks the ASRC/PLL.
    Returns (dev, Fs).
    """
    teardown(old_dev)
    dev, _ = make_dev(uri, buffer_size, fs_low)
    print(f"    re-lock: ODR -> {dev.sampling_frequency} Hz (low), settle {settle}s")
    time.sleep(settle)
    dev.sampling_frequency = fs_high
    Fs = float(dev.sampling_frequency)
    print(f"    re-lock: ODR -> {Fs:.0f} Hz (high, >500 SPS jump -> ASRC re-lock), settle {settle}s")
    time.sleep(settle)
    return dev, Fs


def cluster(means, half_rung=10.0):
    """Group means into clusters (values within half_rung ns of a center).

    Returns list of (center_ns, count) sorted by center.
    """
    clusters = []  # list of [members]
    for m in sorted(means):
        for c in clusters:
            if abs(m - np.mean(c)) <= half_rung:
                c.append(m)
                break
        else:
            clusters.append([m])
    return [(float(np.mean(c)), len(c)) for c in clusters]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    digonly = "--digonly" in sys.argv[1:]

    my_uri  = args[0] if len(args) >= 1 else "ip:analog.local"
    n_iter  = int(args[1]) if len(args) >= 2 else 20
    fs_high = int(args[2]) if len(args) >= 3 else 1400000
    fs_low  = int(args[3]) if len(args) >= 4 else 100000

    ch_a = 0    # reference  (adc_0, chip A)
    ch_b = 4    # compare    (adc_1, chip B)
    buffer_size = 65534
    n_captures  = 5
    settle      = 2.0   # s, per ODR step (driver uses 1 s for PLL+filter; be generous)

    print("=" * 70)
    print("AD7134 within-boot ASRC re-lock test")
    print("=" * 70)
    print(f"URI        : {my_uri}")
    print(f"Iterations : {n_iter}  (NO reboot — §E handover is fixed for this boot)")
    print(f"Mode       : {'DIG_IF_RESET only (control — rung should NOT move)' if digonly else 'ODR re-lock + DIG_IF_RESET each iteration'}")
    if not digonly:
        print(f"ODR jump   : {fs_low} Hz -> {fs_high} Hz  ({(fs_high - fs_low) / 1e3:.0f} kSPS >> 500 SPS)")
    print(f"Settle     : {settle:.1f} s per ODR step")
    print("=" * 70)

    dev, Fs = make_dev(my_uri, buffer_size, fs_high)
    print(f"Fs = {Fs:.6g} Hz\n")

    results = []   # list of (iteration, mean_ns, std_ns)

    for it in range(1, n_iter + 1):
        print(f"{'─' * 70}")
        print(f"Iteration {it}/{n_iter}")
        print(f"{'─' * 70}")

        if digonly:
            print("    control: NO ODR change (frame-counter reset only)")
        else:
            dev, Fs = relock(dev, my_uri, buffer_size, fs_low, fs_high, settle)

        # Prime, reset the digital interface frame counter, then re-prime.
        dev.rx()
        dev.rx_destroy_buffer()
        dev.sync()
        for _ in range(3):
            dev.rx()
        print("    >> DIG_IF_RESET sent")

        delays = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "M")
        mean = float(np.mean(delays))
        std  = float(np.std(delays))
        print(f"    iter {it}: delay = {mean:+.1f} ns (std={std:.1f} ns)\n")
        results.append((it, mean, std))

    # ── Per-iteration table ──────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("  PER-ITERATION")
    print(f"{'=' * 70}")
    print(f"  {'Iter':>5}   {'Delay mean (ns)':>15}   {'Within-iter std':>15}")
    print(f"  {'-' * 5}   {'-' * 15}   {'-' * 15}")
    for it, m, s in results:
        print(f"  {it:>5}   {m:>+15.1f}   {s:>15.1f}")

    means = [m for _, m, _ in results]

    # ── Clustering: how many rungs did we visit this boot? ───────────
    cl = cluster(means)
    print(f"\n{'=' * 70}")
    print("  RUNGS VISITED THIS BOOT")
    print(f"{'=' * 70}")
    print(f"  {'center (ns)':>12}   {'count':>5}")
    print(f"  {'-' * 12}   {'-' * 5}")
    for center, count in cl:
        print(f"  {center:>+12.1f}   {count:>5}")
    spread = (max(means) - min(means)) if means else 0.0
    print(f"\n  rung-to-rung spread = {spread:.1f} ns "
          f"(1 XTAL cycle @ 48 MHz = 20.8 ns)")

    # ── Verdict ──────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("  VERDICT")
    print(f"{'=' * 70}")
    if len(cl) <= 1:
        print("  Rung is FIXED across all re-locks this boot.")
        print("  -> The ±1-cycle latch is set ONCE at the §E RC->crystal handover")
        print("     (hypothesis A').  Re-locking does NOT re-roll it.")
        print("     Fix lives in clkin_aligner HDL (handover retry).")
    else:
        print(f"  Rung MOVED across {len(cl)} clusters within a single boot.")
        print("  -> The ±1-cycle latch is set at the ASRC/PLL re-lock, downstream")
        print("     of §E (hypothesis B).  This is why the probe-order / both-reset")
        print("     §E A/B came back null — §E cannot move a latch set later.")
        print("     Fix is detect-and-retry the lock, or MPC_CONFIG fine-trim.")
        if digonly:
            print("\n  NOTE: this was --digonly (no ODR change) yet the rung still moved.")
            print("  That is unexpected — DIG_IF_RESET alone should not re-lock.")
            print("  Re-check the sync path before trusting the relock-mode result.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
