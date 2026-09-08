# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 — TDD-synchronized DMA capture and inter-channel phase measurement.

A sinewave connected to J11 (distributed to all four ADC inputs) is used to
measure the phase offset between channels B/C/D relative to channel A.  If the
four DMAs start on the same TDD clock edge the phase differences should be ~0°.

Usage:
  python3 ada4356_quad_example.py ip:192.168.2.1
  python3 ada4356_quad_example.py ip:192.168.2.1 65536
  python3 ada4356_quad_example.py ip:192.168.2.1 65536 1000000
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

uri = sys.argv[1] if len(sys.argv) > 1 else "ip:192.168.2.1"
buffer_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 65536
sine_freq_hz = float(sys.argv[3]) if len(sys.argv) > 3 else 1_000_000.0

TDD_CLOCK_HZ = 125_000_000

# Connect
dev = adi.ada4356_quad(uri=uri)
dev.rx_buffer_size = buffer_samples
fs = dev.sampling_frequency

TDD_ON_BASE  = 100
TDD_OFF_BASE = 200

# Configure TDD — 1-second frame, all four DMA sync pulses fire at cycle 100.
# The 1-second frame gives all four Python threads plenty of time to arm and
# wait for the next rising edge, matching the dual-board ZCU102 approach.
tdd = dev.tdd
tdd.enable = False
tdd.burst_count = 0
tdd.frame_length_raw = TDD_CLOCK_HZ  # 1 s
tdd.channel[0].enable = False
for ch_idx in range(1, 5):
    tdd.channel[ch_idx].on_raw  = TDD_ON_BASE
    tdd.channel[ch_idx].off_raw = TDD_OFF_BASE
    tdd.channel[ch_idx].enable  = True
tdd.enable = True
try:
    tdd.sync_soft = True
except Exception:
    pass

time.sleep(0.3)

# Synchronized capture — all four DMAs armed concurrently, start on same TDD pulse
data = dev.rx()

labels = ["A", "B", "C", "D"]
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]

# FFT of all channels — DC-remove first so the signal bin dominates
N = buffer_samples
window = np.hanning(N)
ac = [ch.astype(np.float64) - np.mean(ch) for ch in data]
spectra = [np.fft.rfft(a * window) for a in ac]
freq_axis = np.fft.rfftfreq(N, d=1.0 / fs)

# Fundamental bin — use the known input frequency, not argmax, so that a
# strong spurious elsewhere cannot corrupt the phase measurement.
fund_bin = int(round(sine_freq_hz * N / fs))
fund_freq = freq_axis[fund_bin]

# Phase of each channel at the fundamental bin
phases = [np.angle(s[fund_bin], deg=True) for s in spectra]

# Phase and desync relative to channel A
print(f"\nSampling frequency : {fs / 1e6:.3f} MHz")
print(f"Buffer size        : {buffer_samples} samples ({buffer_samples / fs * 1e3:.3f} ms)")
print(f"Sine frequency     : {sine_freq_hz / 1e3:.3f} kHz  (bin {fund_bin}, axis: {fund_freq / 1e3:.3f} kHz)")
print(f"\n{'Ch':>3}  {'phase (deg)':>12}  {'offset vs A (deg)':>18}  {'desync (samples)':>17}  {'desync (ns)':>12}")
for i, (label, ph) in enumerate(zip(labels, phases)):
    offset_deg = (ph - phases[0] + 180) % 360 - 180
    desync_samples = offset_deg / 360.0 * (fs / sine_freq_hz)
    desync_ns = desync_samples / fs * 1e9
    print(
        f"{label:>3}  {ph:>12.2f}  {offset_deg:>18.2f}  {desync_samples:>17.4f}  {desync_ns:>12.3f}"
    )

print(f"\n{'Ch':>3}  {'mean':>10}  {'std':>10}  {'min':>10}  {'max':>10}")
for label, ch_data in zip(labels, data):
    print(
        f"{label:>3}  {np.mean(ch_data):>10.1f}  {np.std(ch_data):>10.1f}"
        f"  {int(np.min(ch_data)):>10}  {int(np.max(ch_data)):>10}"
    )

# Plot — time domain (zoomed to 5 sine periods) + FFT
zoom_n = min(int(fs / fund_freq * 5), N)
t_us = np.arange(zoom_n) / fs * 1e6
freq_mhz = freq_axis / 1e6

fig, axes = plt.subplots(2, 1, figsize=(14, 9))

for a, label, color in zip(ac, labels, colors):
    axes[0].plot(t_us, a[:zoom_n], label=f"Ch {label}", color=color, linewidth=0.7)
axes[0].set_xlabel("Time (µs)")
axes[0].set_ylabel("ADC codes (DC removed)")
axes[0].set_title(
    f"TDD-synchronized capture — {sine_freq_hz / 1e3:.1f} kHz — 5 periods"
)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

for s, label, color in zip(spectra, labels, colors):
    psd = 20 * np.log10(np.abs(s) * 2 / N / 8192 + 1e-20)
    axes[1].plot(freq_mhz, psd, label=f"Ch {label}", color=color, linewidth=0.7)
axes[1].set_xlabel("Frequency (MHz)")
axes[1].set_ylabel("dBFS")
axes[1].set_title("FFT")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("/tmp/ada4356_quad.png", dpi=150)
print("\nPlot saved: /tmp/ada4356_quad.png")

for ch in dev.channels:
    ch.rx_destroy_buffer()
