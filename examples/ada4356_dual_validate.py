# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Dual ADA4356 — Synchronization validation experiments.

Experiment 1 (TDD offset sweep): injects known integer-sample delays via
the TDD ch2.on_raw offset and verifies the FFT phase method detects them.

Experiment 2 (sync vs random): compares the desync distribution when both
DMAs fire on the same TDD tick vs when ch2 fires at a large random offset,
proving TDD synchronization is real.

Usage:
  python3 ada4356_dual_validate.py ip:192.168.2.1
  python3 ada4356_dual_validate.py ip:192.168.2.1 65536 20000
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

uri            = sys.argv[1] if len(sys.argv) > 1 else "ip:192.168.2.1"
buffer_samples = int(sys.argv[2])   if len(sys.argv) > 2 else 65536
sine_freq_hz   = float(sys.argv[3]) if len(sys.argv) > 3 else 20_000.0

TDD_CLOCK_HZ   = 125_000_000
TDD_ON_BASE    = 100
TDD_OFF_BASE   = TDD_ON_BASE + 100

# Maximum random offset for Exp 2 "unsynchronized" case.
# Must be < frame_length_raw and leave room for the off_raw window.
RANDOM_OFFSET_MAX = 62_500_000   # 0.5 s worth of TDD ticks

# ── helpers ───────────────────────────────────────────────────────────────────

def _phase_to_delay(d0, d1, fs):
    N      = min(len(d0), len(d1))
    d0     = d0[:N].astype(np.float64) - np.mean(d0[:N])
    d1     = d1[:N].astype(np.float64) - np.mean(d1[:N])
    window = np.hanning(N)
    D0     = np.fft.rfft(d0 * window)
    D1     = np.fft.rfft(d1 * window)
    freq_axis  = np.fft.rfftfreq(N, d=1.0 / fs)
    fund_bin   = np.argmax(np.abs(D0[1:])) + 1
    fund_freq  = freq_axis[fund_bin]
    phase0     = np.angle(D0[fund_bin], deg=True)
    phase1     = np.angle(D1[fund_bin], deg=True)
    phase_diff = (phase1 - phase0 + 180) % 360 - 180
    return phase_diff / 360.0 * (fs / fund_freq), fund_freq


def _arm_tdd(dev, ch2_on_raw):
    tdd = dev.tdd
    tdd.enable = False
    tdd.burst_count = 0
    tdd.frame_length_raw       = TDD_CLOCK_HZ
    tdd.channel[1].on_raw      = TDD_ON_BASE
    tdd.channel[1].off_raw     = TDD_OFF_BASE
    tdd.channel[1].enable      = True
    tdd.channel[2].on_raw      = ch2_on_raw
    tdd.channel[2].off_raw     = ch2_on_raw + 100
    tdd.channel[2].enable      = True
    tdd.enable = True
    try:
        tdd.sync_soft = True
    except Exception:
        pass
    time.sleep(0.3)


def measure_delay(dev, ch2_on_raw):
    """Arm TDD with ch2 at ch2_on_raw, capture, return (delay_samples, fund_freq)."""
    _arm_tdd(dev, ch2_on_raw)
    data0, data1 = dev.rx_synced()
    fs = float(dev.board0.sampling_frequency)
    return _phase_to_delay(data0, data1, fs)


def measure_delay_random(dev):
    """Fire ch2 at a random large offset — simulates unsynchronized DMAs.

    TDD stays enabled (required for SYNC_TRANSFER_START=1 bitstream).
    The random offset makes the two DMA start times unpredictable.
    """
    offset = np.random.randint(1000, RANDOM_OFFSET_MAX)
    return measure_delay(dev, TDD_ON_BASE + offset)[0]


# ── connect ───────────────────────────────────────────────────────────────────

dev = adi.ada4356_dual(uri=uri)
dev.board0.rx_enabled_channels = [0]
dev.board1.rx_enabled_channels = [0]
dev.board0.rx_buffer_size = buffer_samples
dev.board1.rx_buffer_size = buffer_samples
fs = float(dev.board0.sampling_frequency)

# ── Experiment 1: TDD offset sweep ───────────────────────────────────────────

offsets  = list(range(6))   # 0..5 TDD ticks = 0..5 samples at 125 MHz
measured = []
expected = []

print("=" * 60)
print("Experiment 1 — TDD offset sweep (1 tick = 1 sample = 8 ns)")
print(f"{'Offset (ticks)':>16}  {'Expected (samp)':>15}  {'Measured (samp)':>15}")
print("-" * 60)

baseline = None
for k in offsets:
    delay, fund_freq = measure_delay(dev, TDD_ON_BASE + k)
    if baseline is None:
        baseline = delay
    measured.append(delay)
    exp = baseline + k
    expected.append(exp)
    print(f"{k:>16d}  {exp:>+15.4f}  {delay:>+15.4f}")

residuals = [m - e for m, e in zip(measured, expected)]
print("-" * 60)
print(f"  Detected fundamental: {fund_freq/1e3:.3f} kHz")
print(f"  Residual std: {np.std(residuals):.4f} samples")
print(f"  Max residual: {max(abs(r) for r in residuals):.4f} samples")

# ── Experiment 2: synchronized vs random-offset distribution ──────────────────

N_TRIALS = 30

print()
print("=" * 60)
print(f"Experiment 2 — synchronized vs random offset ({N_TRIALS} captures each)")

delays_sync   = []
delays_random = []

for i in range(N_TRIALS):
    d, _ = measure_delay(dev, TDD_ON_BASE)
    delays_sync.append(d)
    print(f"  [SYNC  ] trial {i+1:2d}: {d:+.4f} samples", end="\r")
print()

for i in range(N_TRIALS):
    d = measure_delay_random(dev)
    delays_random.append(d)
    print(f"  [RANDOM] trial {i+1:2d}: {d:+.4f} samples", end="\r")
print()

std_sync   = np.std(delays_sync)
std_random = np.std(delays_random)
print(f"  SYNC   — mean: {np.mean(delays_sync):+.4f}  std: {std_sync:.4f} samples")
print(f"  RANDOM — mean: {np.mean(delays_random):+.4f}  std: {std_random:.4f} samples")
print(f"  Std ratio RANDOM/SYNC: {std_random / max(std_sync, 1e-9):.1f}x")

# ── Plot ──────────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Exp 1
axes[0].plot(offsets, expected, "k--", label="Ideal (slope = 1)")
axes[0].plot(offsets, measured, "o-",  color="tab:blue", label="Measured")
axes[0].set_xlabel("ch2.on_raw offset (TDD ticks = samples)")
axes[0].set_ylabel("Measured delay (samples)")
axes[0].set_title(
    f"Exp 1 — TDD offset sweep\n"
    f"residual std = {np.std(residuals):.4f} samples"
)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Exp 2
all_delays = delays_sync + delays_random
bins = np.linspace(min(all_delays), max(all_delays), 25)
axes[1].hist(delays_sync,   bins=bins, alpha=0.7,
             label=f"Synchronized  (std={std_sync:.4f})", color="tab:green")
axes[1].hist(delays_random, bins=bins, alpha=0.7,
             label=f"Random offset (std={std_random:.4f})", color="tab:red")
axes[1].set_xlabel("Measured delay (samples)")
axes[1].set_ylabel("Count")
axes[1].set_title(
    f"Exp 2 — Sync vs random\n"
    f"RANDOM/SYNC std ratio = {std_random/max(std_sync,1e-9):.1f}x"
)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("/tmp/ada4356_dual_validate.png", dpi=150)
print()
print("Plot saved: /tmp/ada4356_dual_validate.png")

dev.board0.rx_destroy_buffer()
dev.board1.rx_destroy_buffer()
