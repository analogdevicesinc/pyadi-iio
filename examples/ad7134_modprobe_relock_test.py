# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# AD7134 modprobe (driver-reload) re-lock test.
#
# Question this answers:
#   Re-running §E via a driver reload re-runs the RC->crystal handover but
#   does NOT power-cycle the chip.  Does that re-roll the inter-chip
#   ±1-XTAL-cycle rung?
#
# Why it matters (this is the decisive one):
#   - Rung CHANGES across modprobe cycles -> the handover latch is
#     re-rollable in software, with no power cycle.  A DRIVER-ONLY retry
#     fix becomes possible: re-run §E in a loop until both chips land on
#     the same rung.  No HDL / bitstream change needed.
#   - Rung STAYS the same as the boot -> the latch is set at true power-on
#     (POR) and a pin-reset/§E does not re-randomize it.  Software §E-retry
#     is dead; you need a power cycle or the HDL dig_clk-feedback path.
#
#   Companion to ad7134_relock_test.py, which already showed the rung is
#   FIXED through ASRC re-locks within a boot (latch is upstream of the
#   re-lock).  This script tests the next stage up: the handover itself.
#
# Prerequisite:
#   The driver MUST be built as a module (CONFIG_AD4134=m) and installed
#   per AD4134_MODULE_TODO.md §1.  With CONFIG_AD4134=y (built-in) rmmod
#   will fail and this test cannot run.
#
# Usage:
#   python ad7134_modprobe_relock_test.py <uri> [n_iter] [fs_high]
#
# Example:
#   python ad7134_modprobe_relock_test.py ip:10.48.65.161 15
#
# Requirements:
#   - Passwordless SSH to root@<host> (ssh-copy-id root@<host>)
#   - ad4134 installed as a module; iiod managed by systemd
#   - A common tone into chip A ch0 and chip B ch4 (low freq ~20 kHz)

import subprocess
import sys
import time

import numpy as np

import adi


def ssh(host, cmd, timeout=30):
    """Run a command on the target over SSH, return (rc, stdout)."""
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
         f"root@{host}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode, r.stdout.strip()


def reload_driver(host, settle_timeout=60):
    """rmmod + modprobe (re-runs §E), then wait until the master re-locks.

    Mirrors the simple reload in ad7134_phase_sync_demo.py: a single
    combined rmmod;modprobe over SSH, with iiod left running untouched
    (no `systemctl stop/restart`, no `fuser -k`).  Those extra steps were
    the suspected trigger for the master double-probe / second-§E timeout.

    The chip is NOT power-cycled — only the driver's reset+§E handover
    re-runs.  Returns the §E DIV32 this reload logged (int or None).
    """
    rc, out = ssh(host, "rmmod ad4134 2>/dev/null; modprobe ad4134", timeout=60)
    if rc != 0:
        raise RuntimeError(f"rmmod/modprobe failed rc={rc}: {out}")

    # Wait until probe finished and the master PLL is locked.
    # iio_reg uses the board-local backend, so it works regardless of iiod.
    print("    waiting for §E + PLL lock", end="", flush=True)
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

    # iiod was started at boot and holds a stale device list; restart it so
    # the network context (ip: URI) re-enumerates the freshly probed adc_0/1.
    # Safe for the probe — it's userspace and does not re-bind the SPI driver.
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
    return f0, np.degrees(phi), -phi / (2 * np.pi * f0) * 1e9


def measure_delays(dev, ch_a, ch_b, Fs, n_captures, label):
    delays = []
    for i in range(n_captures):
        data = dev.rx()
        x = np.array(data[ch_a], dtype=np.float64)
        y = np.array(data[ch_b], dtype=np.float64)
        f0, phase_deg, delay_ns = compute_phase_delay(x, y, Fs)
        delays.append(delay_ns)
        print(f"    [{label} {i + 1}]  f0={f0:.1f} Hz  phase={phase_deg:+.3f} deg  delay={delay_ns:+.1f} ns")
    return delays


def cluster(means, half_rung=10.0):
    clusters = []
    for m in sorted(means):
        for c in clusters:
            if abs(m - np.mean(c)) <= half_rung:
                c.append(m)
                break
        else:
            clusters.append([m])
    return [(float(np.mean(c)), len(c)) for c in clusters]


def main():
    my_uri  = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    n_iter  = int(sys.argv[2]) if len(sys.argv) >= 3 else 15
    fs_high = int(sys.argv[3]) if len(sys.argv) >= 4 else 1400000

    if not my_uri.startswith("ip:"):
        print("ERROR: URI must start with 'ip:' for SSH driver reload.")
        sys.exit(1)
    host = my_uri[3:]

    ch_a, ch_b = 0, 4
    buffer_size = 65534
    n_captures  = 5

    print("=" * 70)
    print("AD7134 modprobe (driver-reload) re-lock test")
    print("=" * 70)
    print(f"URI        : {my_uri}")
    print(f"Iterations : {n_iter}  (each = rmmod + modprobe = fresh §E handover, NO power cycle)")
    print(f"Target ODR : {fs_high} Hz")
    print("=" * 70)

    results = []   # (iter, div32, mean_ns, std_ns)

    for it in range(1, n_iter + 1):
        print(f"{'─' * 70}")
        print(f"Iteration {it}/{n_iter}")
        print(f"{'─' * 70}")

        div32 = reload_driver(host)
        d_str = f"0x{div32:03x}" if div32 is not None else "N/A"
        print(f"    §E DIV32 = {d_str}")

        dev = adi.ad7134(uri=my_uri)
        dev.rx_enabled_channels = list(range(8))
        dev.rx_buffer_size = buffer_size
        dev.sampling_frequency = fs_high
        Fs = float(dev.sampling_frequency)

        dev.rx()
        dev.rx_destroy_buffer()
        dev.sync()
        for _ in range(3):
            dev.rx()
        print("    >> DIG_IF_RESET sent")

        delays = measure_delays(dev, ch_a, ch_b, Fs, n_captures, "M")
        mean = float(np.mean(delays))
        std  = float(np.std(delays))
        print(f"    iter {it}: DIV32={d_str}  delay = {mean:+.1f} ns (std={std:.1f} ns)\n")
        results.append((it, div32, mean, std))
        del dev

    # ── Per-iteration table ──────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("  PER-ITERATION")
    print(f"{'=' * 70}")
    print(f"  {'Iter':>5}   {'DIV32':>7}   {'Delay mean (ns)':>15}   {'std':>6}")
    print(f"  {'-' * 5}   {'-' * 7}   {'-' * 15}   {'-' * 6}")
    for it, d, m, s in results:
        ds = f"0x{d:03x}" if d is not None else "N/A"
        print(f"  {it:>5}   {ds:>7}   {m:>+15.1f}   {s:>6.1f}")

    means = [m for _, _, m, _ in results]
    cl = cluster(means)

    print(f"\n{'=' * 70}")
    print("  RUNGS VISITED ACROSS MODPROBE CYCLES")
    print(f"{'=' * 70}")
    print(f"  {'center (ns)':>12}   {'count':>5}")
    print(f"  {'-' * 12}   {'-' * 5}")
    for center, count in cl:
        print(f"  {center:>+12.1f}   {count:>5}")
    spread = (max(means) - min(means)) if means else 0.0
    print(f"\n  rung-to-rung spread = {spread:.1f} ns "
          f"(1 XTAL cycle @ 48 MHz = 20.8 ns)")

    print(f"\n{'=' * 70}")
    print("  VERDICT")
    print(f"{'=' * 70}")
    if len(cl) <= 1:
        print("  Rung is FIXED across all driver reloads.")
        print("  -> A pin-reset/§E handover does NOT re-roll the latch; it is set at")
        print("     true power-on (POR).  Software §E-retry will NOT work.")
        print("     Need a power cycle or the HDL dig_clk-feedback fix.")
    else:
        print(f"  Rung MOVED across {len(cl)} clusters via driver reload alone.")
        print("  -> The handover latch IS re-rollable in software, no power cycle.")
        print("     A DRIVER-ONLY retry fix is viable: re-run §E until both chips")
        print("     land on the same rung.  No HDL / bitstream change required.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
