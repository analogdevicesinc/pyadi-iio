# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Dual ADA4356 — TDD-synchronized DMA capture and phase measurement.

Usage:
  python3 ada4356_dual_example.py ip:192.168.2.1
  python3 ada4356_dual_example.py ip:192.168.2.1 65536 200000
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

uri = sys.argv[1] if len(sys.argv) > 1 else "ip:192.168.2.1"
buffer_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 65536
sine_freq_hz = float(sys.argv[3]) if len(sys.argv) > 3 else 200_000.0

TDD_CLOCK_HZ = 125_000_000

# Connect
dev = adi.ada4356_dual(uri=uri)
dev.board0.rx_enabled_channels = [0]
dev.board1.rx_enabled_channels = [0]
dev.board0.rx_buffer_size = buffer_samples
dev.board1.rx_buffer_size = buffer_samples
fs = float(dev.board0.sampling_frequency)

# Configure TDD — channels 1 and 2 pulse at the same clock cycle
tdd = dev.tdd
tdd.enable = False
tdd.burst_count = 0
tdd.frame_length_raw = TDD_CLOCK_HZ  # 1 second frame
tdd.channel[1].on_raw = 100
tdd.channel[1].off_raw = 200
tdd.channel[1].enable = True
tdd.channel[2].on_raw = 100
tdd.channel[2].off_raw = 200
tdd.channel[2].enable = True
tdd.enable = True
try:
    tdd.sync_soft = True
except Exception:
    pass

time.sleep(0.3)

# Synchronized capture — both DMAs armed concurrently, start on same TDD pulse
data0, data1 = dev.rx_synced()

# Phase measurement via FFT
N = min(len(data0), len(data1))
d0 = data0[:N].astype(np.float64) - np.mean(data0[:N])
d1 = data1[:N].astype(np.float64) - np.mean(data1[:N])

window = np.hanning(N)
D0 = np.fft.rfft(d0 * window)
D1 = np.fft.rfft(d1 * window)

freq_axis = np.fft.rfftfreq(N, d=1.0 / fs)
fund_bin = np.argmax(np.abs(D0[1:])) + 1
fund_freq = freq_axis[fund_bin]

phase0 = np.angle(D0[fund_bin], deg=True)
phase1 = np.angle(D1[fund_bin], deg=True)
phase_diff = (phase1 - phase0 + 180) % 360 - 180

print(f"Fundamental:  {fund_freq / 1e3:.3f} kHz")
print(f"Board 0 phase: {phase0:.2f} deg")
print(f"Board 1 phase: {phase1:.2f} deg")
print(f"Phase offset (board1 - board0): {phase_diff:.2f} deg")

# Sample-level desynchronization — Method 1: FFT phase (sub-sample, best for sinewaves)
delay_samples_fft = phase_diff / 360.0 * (fs / fund_freq)
delay_ns_fft = delay_samples_fft / fs * 1e9

# Sample-level desynchronization — Method 2: cross-correlation (integer sample)
# Search within ±half period only to avoid the periodic cosine peaks of a sinewave xcorr
half_period_n = int(fs / fund_freq / 2)
xcorr = np.correlate(d0 / (np.std(d0) + 1e-12), d1 / (np.std(d1) + 1e-12), mode="full")
lags = np.arange(-(N - 1), N)
center = N - 1
lo = max(0, center - half_period_n)
hi = min(len(xcorr), center + half_period_n + 1)
delay_xcorr = int(lags[lo + np.argmax(xcorr[lo:hi])])

print(
    f"Desync (FFT phase):  {delay_samples_fft:+.4f} samples  ({delay_ns_fft:+.3f} ns)"
)
print(f"Desync (cross-corr): {delay_xcorr:+d} samples (integer)")

# Simple plot
fig, axes = plt.subplots(3, 1, figsize=(12, 9))

zoom_n = min(int(fs / fund_freq * 20), N)
t_us = np.arange(zoom_n) / fs * 1e6
axes[0].plot(t_us, d0[:zoom_n], label="Board 0")
axes[0].plot(t_us, d1[:zoom_n], label="Board 1", alpha=0.8)
axes[0].set_xlabel("Time (µs)")
axes[0].set_ylabel("ADC codes (DC removed)")
axes[0].set_title(
    f"TDD-synchronized capture — {fund_freq/1e3:.1f} kHz — phase offset: {phase_diff:.2f}°"
)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

freq_mhz = freq_axis / 1e6
axes[1].plot(
    freq_mhz, 20 * np.log10(np.abs(D0) * 2 / N / 8192 + 1e-20), label="Board 0"
)
axes[1].plot(
    freq_mhz,
    20 * np.log10(np.abs(D1) * 2 / N / 8192 + 1e-20),
    label="Board 1",
    alpha=0.8,
)
axes[1].set_xlabel("Frequency (MHz)")
axes[1].set_ylabel("dBFS")
axes[1].set_title("FFT")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Cross-correlation around lag=0 (±5 periods for visibility)
view = min(int(fs / fund_freq * 5), half_period_n)
axes[2].plot(
    lags[center - view : center + view + 1], xcorr[center - view : center + view + 1]
)
axes[2].axvline(
    delay_xcorr,
    color="r",
    linestyle="--",
    label=f"xcorr peak: {delay_xcorr:+d} samples",
)
axes[2].axvline(
    delay_samples_fft,
    color="g",
    linestyle="--",
    label=f"FFT phase:  {delay_samples_fft:+.3f} samples",
)
axes[2].set_xlabel("Lag (samples)")
axes[2].set_ylabel("Normalized xcorr")
axes[2].set_title(
    f"Cross-correlation — desync: {delay_samples_fft:+.4f} samples / {delay_ns_fft:+.3f} ns"
)
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("/tmp/ada4356_dual.png", dpi=150)
print("Plot saved: /tmp/ada4356_dual.png")

dev.board0.rx_destroy_buffer()
dev.board1.rx_destroy_buffer()
