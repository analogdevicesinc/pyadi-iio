# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 modprobe sync test (fast stand-in for ad7134_reboot_test.py).
#
# Same experiment as ad7134_reboot_test.py — measure the inter-chip delay
# BEFORE and AFTER DIG_IF_RESET on each cycle — but instead of physically
# rebooting the board, it reloads the kernel driver (rmmod + modprobe).
#
# A driver reload re-runs §E (chip /RESETN pulse + RC->crystal handover) and
# therefore re-rolls the inter-chip ±1-XTAL-cycle rung, just like a reboot —
# but in ~3 s instead of ~30-120 s.  It does NOT reload the FPGA bitstream
# and does NOT power-cycle the chips, so it exercises the driver/§E/§F/sync
# path, not the full boot or supply ramp.
#
# Prerequisite: ad4134 built as a module (CONFIG_AD4134=m) AND the driver
# must include the §E.0 clkin_aligner FSM soft-reset, or the 2nd reload
# onward hangs in §E (startup_done TIMEOUT, adc_0 never comes up).
#
# Usage:
#   python ad7134_modprobe_test.py <uri> [n_iter] [target_fs]
#
# Examples:
#   python ad7134_modprobe_test.py ip:10.48.65.161
#   python ad7134_modprobe_test.py ip:10.48.65.161 10
#   python ad7134_modprobe_test.py ip:10.48.65.161 10 1400000
#
# Requirements:
#   - Passwordless SSH to root@<host> (run: ssh-copy-id root@<host>)
#   - ad4134 installed as a module; iiod managed by systemd

import subprocess
import sys
import time

import numpy as np

import adi


def ssh(host, cmd, timeout=60):
    """Run a command on the target over SSH, return (rc, stdout)."""
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
         f"root@{host}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode, r.stdout.strip()


def reload_driver(host, settle_timeout=60):
    """rmmod + modprobe (re-runs §E), then wait until the master re-locks.

    A single combined rmmod;modprobe over SSH, with iiod left running.
    The chip is NOT power-cycled — only the driver's reset+§E handover
    re-runs, which re-rolls the inter-chip rung.  Returns §E DIV32 (or None).
    """
    # rmmod and modprobe as separate timed steps so each is visible.
    t0 = time.monotonic()
    print(f"  [{time.strftime('%H:%M:%S')}] rmmod ad4134 ...", flush=True)
    rc, out = ssh(host, "rmmod ad4134", timeout=60)
    t_rmmod = time.monotonic()
    if rc != 0:
        print(f"  [{time.strftime('%H:%M:%S')}] WARN: rmmod rc={rc}: {out} "
              "(module may have been busy — iteration could measure stale state)")
    print(f"  [{time.strftime('%H:%M:%S')}] rmmod took effect "
          f"(+{t_rmmod - t0:.1f}s)", flush=True)

    print(f"  [{time.strftime('%H:%M:%S')}] modprobe ad4134 ... "
          "(blocks through §E/§F init)", flush=True)
    rc, out = ssh(host, "modprobe ad4134", timeout=60)
    t_modprobe = time.monotonic()
    if rc != 0:
        raise RuntimeError(f"modprobe failed rc={rc}: {out}")
    print(f"  [{time.strftime('%H:%M:%S')}] modprobe returned, probe done "
          f"(+{t_modprobe - t_rmmod:.1f}s)", flush=True)

    # Wait until probe finished and the master PLL is locked.
    # iio_reg uses the board-local backend, so it works regardless of iiod.
    print("  Waiting for §E + PLL lock", end="", flush=True)
    t0 = time.monotonic()
    while time.monotonic() - t0 < settle_timeout:
        rc, out = ssh(host, "iio_reg adc_0 0x15 2>/dev/null")
        if rc == 0 and out.strip() in ("0x1", "0x01", "1"):
            print(f"  ready after {time.monotonic() - t0:.0f} s")
            break
        print(".", end="", flush=True)
        time.sleep(2)
    else:
        print()
        raise TimeoutError("driver did not become ready after reload")

    # iiod holds a stale device list across the reload; restart so the ip:
    # context re-enumerates the freshly probed adc_0/1.  Userspace only —
    # does not re-bind the SPI driver.
    ssh(host, "systemctl restart iiod")
    time.sleep(2)

    # Read the §E DIV32 this reload logged, for context.
    _, d = ssh(host,
               "dmesg | grep 'startup_done IRQ' "
               "| grep -oP 'DIV32=0x\\K[0-9a-fA-F]{8}' | tail -1")
    try:
        return int(d, 16) if d else None
    except ValueError:
        return None


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


def main():
    my_uri    = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    n_iter    = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
    target_fs = int(sys.argv[3]) if len(sys.argv) >= 4 else 1400000

    ch_a = 0    # reference  (adc_0, chip A)
    ch_b = 4    # compare    (adc_1, chip B)
    buffer_size = 65534
    n_captures  = 5

    if not my_uri.startswith("ip:"):
        print("ERROR: URI must start with 'ip:' for SSH driver reload.")
        sys.exit(1)
    host = my_uri[3:]

    print("=" * 65)
    print("AD7134 modprobe Sync Test (driver-reload stand-in for reboot)")
    print("=" * 65)
    print(f"URI        : {my_uri}")
    print(f"Reloads    : {n_iter}  (each = rmmod + modprobe = fresh §E, NO power cycle)")
    print(f"Target ODR : {target_fs} Hz ({target_fs / 1e6:.3f} MSPS)")
    print(f"Captures   : {n_captures} before + {n_captures} after per reload")
    print("=" * 65)

    results = []   # list of (iter, div32, before_mean, after_mean, after_std)

    for it in range(1, n_iter + 1):
        print(f"\n{'─' * 65}")
        print(f"Reload {it}/{n_iter}")
        print(f"{'─' * 65}")

        div32 = reload_driver(host)
        d_str = f"0x{div32:03x}" if div32 is not None else "N/A"
        print(f"  §E DIV32 = {d_str}")

        dev = adi.ad7134(uri=my_uri)
        dev.rx_enabled_channels = list(range(8))
        dev.rx_buffer_size = buffer_size
        dev.sampling_frequency = target_fs
        Fs = float(dev.sampling_frequency)
        print(f"  Fs = {Fs:.6g} Hz\n")

        # Before sync
        print("  --- BEFORE sync ---")
        before = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "B")
        before_mean = float(np.mean(before))

        # Sync (DIG_IF_RESET)
        dev.rx_destroy_buffer()
        dev.sync()
        for _ in range(3):
            dev.rx()
        print("\n  >> DIG_IF_RESET sent\n")

        # After sync
        print("  --- AFTER sync ---")
        after = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "A")
        after_mean = float(np.mean(after))
        after_std  = float(np.std(after))

        print(f"\n  Reload {it} summary: DIV32={d_str}  before={before_mean:+.1f} ns  "
              f"after={after_mean:+.1f} ns (std={after_std:.1f} ns)  "
              f"(Δ={after_mean - before_mean:+.1f} ns)")

        results.append((it, div32, before_mean, after_mean, after_std))
        del dev

    # ── Final summary table ──────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 78}")
    print(f"  {'Iter':>5}   {'DIV32':>6}   {'Before (ns)':>11}   {'After mean':>10}   {'After std':>9}   {'Delta':>8}")
    print(f"  {'-' * 5}   {'-' * 6}   {'-' * 11}   {'-' * 10}   {'-' * 9}   {'-' * 8}")
    for it, d, bm, am, astd in results:
        ds = f"0x{d:03x}" if d is not None else "N/A"
        print(f"  {it:>5}   {ds:>6}   {bm:>+11.1f}   {am:>+10.1f}   {astd:>9.1f}   {am - bm:>+8.1f}")
    print(f"  {'-' * 5}   {'-' * 6}   {'-' * 11}   {'-' * 10}   {'-' * 9}   {'-' * 8}")

    befores = [r[2] for r in results]
    afters  = [r[3] for r in results]
    astds   = [r[4] for r in results]
    deltas  = [r[3] - r[2] for r in results]
    print(f"  {'mean':>5}   {'':>6}   {np.mean(befores):>+11.1f}   {np.mean(afters):>+10.1f}   {np.mean(astds):>9.1f}   {np.mean(deltas):>+8.1f}")
    print(f"  {'std':>5}   {'':>6}   {np.std(befores):>11.1f}   {np.std(afters):>10.1f}   {'':>9}   {np.std(deltas):>8.1f}")
    print(f"{'=' * 78}")


if __name__ == "__main__":
    main()
