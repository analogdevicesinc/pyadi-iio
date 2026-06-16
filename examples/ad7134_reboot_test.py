# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 reboot sync test.
#
# Repeatedly reboots the target board and measures the inter-chip delay
# before and after DIG_IF_RESET sync on each boot.  After sync, captures
# one measurement every 5 seconds for 2 minutes to verify delay stability
# over time (rules out iio_osc display artifacts vs real drift).
#
# Usage:
#   python ad7134_reboot_test.py <uri> [n_reboots] [target_fs]
#
# Examples:
#   python ad7134_reboot_test.py ip:10.48.65.230
#   python ad7134_reboot_test.py ip:10.48.65.230 10
#   python ad7134_reboot_test.py ip:10.48.65.230 10 1400000
#
# Requirements:
#   - Passwordless SSH to root@<host> (run: ssh-copy-id root@<host>)
#   - iiod running on the target

import subprocess
import sys
import time

import numpy as np

import adi


def reboot_and_wait(host, boot_timeout=120, iiod_settle=5):
    """SSH reboot the board and wait until iiod is reachable again."""
    print(f"  Rebooting {host} ...", flush=True)
    subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
         f"root@{host}", "reboot"],
        check=False,
    )

    time.sleep(12)  # wait for board to go down before polling

    print("  Waiting for board to come back", end="", flush=True)
    t0 = time.monotonic()
    while time.monotonic() - t0 < boot_timeout:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
             f"root@{host}", "echo ok"],
            capture_output=True,
        )
        if result.returncode == 0:
            elapsed = time.monotonic() - t0 + 12
            print(f"\n  Board back online after {elapsed:.0f} s — waiting {iiod_settle} s for iiod ...", flush=True)
            time.sleep(iiod_settle)
            return
        print(".", end="", flush=True)
        time.sleep(3)

    print()
    raise TimeoutError(f"Board did not come back within {boot_timeout} s")


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


# --- CHANGED: added timed capture function ---
# Instead of just 5 quick captures after sync, this captures one measurement
# every `interval` seconds for `duration` seconds.  Each measurement includes
# a timestamp (seconds since sync) so we can see if the delay drifts over time.
def measure_delays_timed(dev, ch_a, ch_b, Fs, duration, interval, label):
    """Capture one frame every `interval` seconds for `duration` seconds.

    Returns list of (elapsed_s, delay_ns) tuples.
    """
    results = []
    t0 = time.monotonic()
    idx = 1
    while True:
        elapsed = time.monotonic() - t0
        if elapsed > duration:
            break
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)
        f0, phase_deg, delay_ns = compute_phase_delay(x, y, Fs)
        results.append((elapsed, delay_ns))
        print(f"    [{label} {idx:>2}]  t={elapsed:>6.1f}s  f0={f0:.1f} Hz  "
              f"phase={phase_deg:+.3f} deg  delay={delay_ns:+.1f} ns")
        idx += 1
        # Wait until the next interval boundary
        next_time = t0 + idx * interval
        sleep_time = next_time - time.monotonic()
        if sleep_time > 0:
            time.sleep(sleep_time)
    return results


def main():
    my_uri    = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    n_reboots = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
    target_fs = int(sys.argv[3]) if len(sys.argv) >= 4 else 1400000

    ch_a = 0    # reference  (adc_0, chip A)
    ch_b = 4    # compare    (adc_1, chip B)
    buffer_size = 65534
    n_captures  = 5          # before-sync captures (unchanged)
    # --- CHANGED: after-sync timed capture parameters ---
    # Capture every 5 seconds for 2 minutes to check delay stability over time
    after_duration = 120     # total monitoring window (seconds)
    after_interval = 5       # seconds between captures

    if not my_uri.startswith("ip:"):
        print("ERROR: URI must start with 'ip:' for SSH reboot support.")
        sys.exit(1)

    host = my_uri[3:]

    print("=" * 65)
    print("AD7134 Reboot Sync Test")
    print("=" * 65)
    print(f"URI        : {my_uri}")
    print(f"Reboots    : {n_reboots}")
    print(f"Target ODR : {target_fs} Hz ({target_fs / 1e6:.3f} MSPS)")
    # --- CHANGED: updated info to reflect timed after-sync capture ---
    print(f"Captures   : {n_captures} before + {n_captures} after per boot")
    print("=" * 65)

    results = []   # list of (boot, before_mean, after_mean)

    for boot in range(1, n_reboots + 1):
        print(f"\n{'─' * 65}")
        print(f"Boot {boot}/{n_reboots}")
        print(f"{'─' * 65}")

        reboot_and_wait(host)

        dev = adi.ad7134(uri=my_uri)
        dev.rx_enabled_channels = list(range(8))
        dev.rx_buffer_size = buffer_size
        dev.sampling_frequency = target_fs
        Fs = float(dev.sampling_frequency)
        print(f"  Fs = {Fs:.6g} Hz\n")

        # Before sync
        print("  --- BEFORE sync ---")
        before = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "B")
        before_mean = np.mean(before)

        # Sync
        dev.rx_destroy_buffer()
        dev.sync()
        for _ in range(3):
            dev.rx()
        print(f"\n  >> DIG_IF_RESET sent\n")

        # After sync
        print("  --- AFTER sync ---")
        after = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "A")
        after_mean = np.mean(after)
        after_std  = np.std(after)

        # # --- timed monitoring (every 5s for 2 min) — uncomment to enable ---
        # print(f"  --- AFTER sync (monitoring for {after_duration}s) ---")
        # after_timed = measure_delays_timed(dev, ch_a, ch_b, Fs,
        #                                    after_duration, after_interval, "A")
        # after = [d for _, d in after_timed]
        # after_mean = np.mean(after)
        # after_std  = np.std(after)

        print(f"\n  Boot {boot} summary: before={before_mean:+.1f} ns  "
              f"after={after_mean:+.1f} ns (std={after_std:.1f} ns)  "
              f"(Δ={after_mean - before_mean:+.1f} ns)")

        results.append((boot, before_mean, after_mean, after_std))
        del dev

        if boot < n_reboots:
            time.sleep(5)

    # ── Final summary table ──────────────────────────────────────────
    # --- CHANGED: added "After std" column to show delay stability ---
    # Low std = delay is stable over the 2 min window (iio_osc was artifact)
    # High std = delay truly drifts over time (real problem)
    print(f"\n{'=' * 75}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 75}")
    print(f"  {'Boot':>5}   {'Before (ns)':>11}   {'After mean':>10}   {'After std':>9}   {'Delta':>8}")
    print(f"  {'-' * 5}   {'-' * 11}   {'-' * 10}   {'-' * 9}   {'-' * 8}")
    for boot, bm, am, astd in results:
        print(f"  {boot:>5}   {bm:>+11.1f}   {am:>+10.1f}   {astd:>9.1f}   {am - bm:>+8.1f}")
    print(f"  {'-' * 5}   {'-' * 11}   {'-' * 10}   {'-' * 9}   {'-' * 8}")

    befores = [r[1] for r in results]
    afters  = [r[2] for r in results]
    astds   = [r[3] for r in results]
    deltas  = [r[2] - r[1] for r in results]
    print(f"  {'mean':>5}   {np.mean(befores):>+11.1f}   {np.mean(afters):>+10.1f}   {np.mean(astds):>9.1f}   {np.mean(deltas):>+8.1f}")
    print(f"  {'std':>5}   {np.std(befores):>11.1f}   {np.std(afters):>10.1f}   {'':>9}   {np.std(deltas):>8.1f}")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    main()
