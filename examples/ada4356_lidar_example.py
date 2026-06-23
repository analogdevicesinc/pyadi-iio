# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""LiDAR Simulation using M2K and ADA4356

Hardware Connections:
  TRIG_SMA_OUT -> M2K TI -> M2K W1 -> ADA4356 BHCS_SMA_IN (J1)

Modes:
  multi  - Many short TDD frames, captures repeated echo pulses (default)
  single - One long frame, captures a single echo pulse in full DMA buffer
  fft    - Continuous sinewave capture + FFT analysis for DMA data integrity

Usage:
  python3 ada4356_lidar_example.py ip:192.168.2.1
  python3 ada4356_lidar_example.py ip:192.168.2.1 50
  python3 ada4356_lidar_example.py ip:192.168.2.1 50 8388608 single
  python3 ada4356_lidar_example.py ip:192.168.2.1 50 65536 fft
  python3 ada4356_lidar_example.py ip:192.168.2.1 50 65536 fft 2000000
"""

import sys
import time

import libm2k
import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import adi

if len(sys.argv) < 2:
    print(
        "Usage: python3 ada4356_lidar_example.py ip:<zedboard_ip> "
        "[distance_m] [buffer_samples] [mode] [sine_freq_hz]"
    )
    print("  mode: 'multi' (default), 'single', or 'fft'")
    print("  sine_freq_hz: sinewave frequency for fft mode (default 1000000)")
    sys.exit(1)

uri = sys.argv[1]
target_distance_m = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
buffer_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 65536
mode = sys.argv[4].lower() if len(sys.argv) > 4 else "multi"
sine_freq_hz = float(sys.argv[5]) if len(sys.argv) > 5 else 1000000

SPEED_OF_LIGHT = 299792458.0
M2K_SAMPLE_RATE = 75000000
TDD_CLOCK_HZ = 125000000
TDD_CLOCK_PERIOD_NS = 8.0
TDD_FRAME_RATE_HZ = 10000
TDD_FRAME_PERIOD_US = 100.0

# TDD channel timing (clock cycles, 1 cycle = 8 ns)
if mode == "single":
    # Frame(t=0) -> DMA sync(t=500us) -> Laser trigger(t=1ms)
    CH0_ON_RAW = 125000
    CH0_OFF_RAW = 125125
    CH1_ON_RAW = 62500
    CH1_OFF_RAW = CH1_ON_RAW + buffer_samples
    frame_length = int(buffer_samples * 1.1)
    TDD_FRAME_PERIOD_US = frame_length * TDD_CLOCK_PERIOD_NS / 1000
    pulse_amplitude_v = 0.5
    print(
        f"SINGLE PULSE MODE: {buffer_samples:,} samples, "
        f"frame = {TDD_FRAME_PERIOD_US / 1000:.1f} ms, "
        f"capture = {buffer_samples / TDD_CLOCK_HZ * 1000:.1f} ms"
    )
elif mode == "fft":
    # Trigger once(t=0.8us) -> M2K starts sinewave -> DMA gate(t=10us) -> fill buffer
    CH0_ON_RAW = 100
    CH0_OFF_RAW = 225
    CH1_ON_RAW = 1250
    CH1_OFF_RAW = CH1_ON_RAW + buffer_samples
    frame_length = int(CH1_OFF_RAW * 1.1)
    TDD_FRAME_PERIOD_US = frame_length * TDD_CLOCK_PERIOD_NS / 1000
    pulse_amplitude_v = 0.5
    print(
        f"FFT MODE: {buffer_samples:,} samples, "
        f"sine = {sine_freq_hz / 1e6:.3f} MHz, "
        f"frame = {TDD_FRAME_PERIOD_US / 1000:.1f} ms"
    )
else:
    # Frame/DMA gate(t=0) -> Trigger(t=10us) -> DMA gate close(t=20us)
    CH0_ON_RAW = 1250
    CH0_OFF_RAW = 1375
    CH1_ON_RAW = 625
    CH1_OFF_RAW = 11875
    frame_length = int(TDD_CLOCK_HZ / TDD_FRAME_RATE_HZ)
    pulse_amplitude_v = 2.0
    print(
        f"MULTI PULSE MODE: {buffer_samples:,} samples across "
        f"{buffer_samples * TDD_CLOCK_PERIOD_NS / 1000 / TDD_FRAME_PERIOD_US:.0f} frames"
    )

echo_delay_us = (2 * target_distance_m / SPEED_OF_LIGHT) * 1e6
pulse_width_us = 10.0
offset_v = 2.0

print(
    f"LiDAR Simulation: {target_distance_m} m target, {echo_delay_us:.3f} us echo delay"
)

# Connect to M2K
m2k = libm2k.m2kOpen()
if not m2k:
    print("ERROR: M2K not found")
    sys.exit(1)
m2k.calibrateADC()
m2k.calibrateDAC()

# Connect to ADA4356
try:
    lidar = adi.ada4356_lidar(uri=uri)
except Exception as e:
    print(f"ERROR: {e}")
    libm2k.contextClose(m2k)
    sys.exit(1)

# Configure TDD
tdd = lidar.tdd
tdd.enable = False
tdd.burst_count = 0
tdd.frame_length_raw = frame_length
tdd.channel[0].on_raw = CH0_ON_RAW
tdd.channel[0].off_raw = CH0_OFF_RAW
tdd.channel[0].enable = True
tdd.channel[1].on_raw = CH1_ON_RAW
tdd.channel[1].off_raw = CH1_OFF_RAW
tdd.channel[1].enable = True
tdd.enable = True
try:
    tdd.sync_soft = True
except Exception:
    pass

# Configure M2K AWG
aout = m2k.getAnalogOut()
actual_rate = aout.setSampleRate(0, M2K_SAMPLE_RATE)
aout.enableChannel(0, True)

trig = aout.getTrigger()
trig.setAnalogSource(libm2k.TRIGGER_TI)
trig.setAnalogCondition(0, libm2k.RISING_EDGE_ANALOG)
trig.setAnalogDelay(0)

# Create waveform
if mode == "single":
    # Sine burst after echo delay
    actual_rate = aout.setSampleRate(0, 10000000)
    frame_samples_m2k = 750000
    burst_duration_us = 100
    delay_samples = int(echo_delay_us * actual_rate / 1e6)
    burst_samples = int(burst_duration_us * actual_rate / 1e6)
    waveform = np.ones(frame_samples_m2k) * offset_v
    burst_end = min(delay_samples + burst_samples, frame_samples_m2k)
    t_burst = np.arange(burst_end - delay_samples) / actual_rate
    sine_freq_burst = 100000
    waveform[delay_samples:burst_end] = offset_v + pulse_amplitude_v * np.sin(
        2 * np.pi * sine_freq_burst * t_burst
    )
    print(
        f"M2K: {frame_samples_m2k:,} samples at {actual_rate/1e6:.0f} MSPS, "
        f"sine burst: {sine_freq_burst/1000:.0f} kHz x {burst_duration_us} us"
    )
elif mode == "fft":
    # Continuous sinewave: one cycle repeated cyclically
    samples_per_cycle = int(round(actual_rate / sine_freq_hz))
    actual_sine_freq = actual_rate / samples_per_cycle
    t_one_cycle = np.arange(samples_per_cycle) / actual_rate
    sine_offset_v = 1.0
    waveform = sine_offset_v + pulse_amplitude_v * np.sin(
        2 * np.pi * actual_sine_freq * t_one_cycle
    )
    print(
        f"M2K: {actual_sine_freq / 1e6:.6f} MHz sinewave, "
        f"{pulse_amplitude_v * 2:.1f} Vpp + {sine_offset_v:.1f} V offset, "
        f"{samples_per_cycle} samples/cycle at {actual_rate / 1e6:.0f} MSPS"
    )
else:
    # Rectangular echo pulse matching frame period
    frame_samples_m2k = int(TDD_FRAME_PERIOD_US * actual_rate / 1e6)
    delay_samples = int(echo_delay_us * actual_rate / 1e6)
    pulse_samples = int(pulse_width_us * actual_rate / 1e6)
    waveform = np.ones(frame_samples_m2k) * offset_v
    pulse_end = min(delay_samples + pulse_samples, frame_samples_m2k)
    waveform[delay_samples:pulse_end] = offset_v + pulse_amplitude_v

aout.setCyclic(True)
aout.push(0, waveform.tolist())

# Capture
adc_sample_rate = float(lidar.sampling_frequency)
lidar.rx_buffer_size = buffer_samples
lidar.rx_enabled_channels = [0]
print(f"Buffer: {buffer_samples:,} samples ({buffer_samples * 2 / 1e6:.1f} MB)")

time.sleep(0.3)

start_time = time.perf_counter()
data = lidar.rx()
capture_duration = (time.perf_counter() - start_time) * 1000

# Invert signal (ADA4356 TIA inverts)
baseline = np.median(data)
data = -(data - baseline)

print(
    f"Captured {len(data):,} samples in {capture_duration:.1f} ms, "
    f"range: {data.max() - data.min():.0f} ADC codes"
)

time_us = np.arange(len(data)) / adc_sample_rate * 1e6
time_ms = time_us / 1000

if mode == "fft":
    # --- Time-domain discontinuity detection ---
    diff = np.diff(data.astype(np.float64))
    diff_std = np.std(diff)
    diff_max = np.max(np.abs(diff))
    expected_max_diff = (
        2 * np.pi * actual_sine_freq / adc_sample_rate * np.std(data) * np.sqrt(2)
    )
    discontinuity_threshold = expected_max_diff * 3
    outliers = np.where(np.abs(diff) > discontinuity_threshold)[0]

    print(f"\n--- Time-Domain Integrity ---")
    print(
        f"Sample diff: std={diff_std:.1f}, max={diff_max:.1f}, "
        f"threshold={discontinuity_threshold:.1f}"
    )
    if len(outliers) == 0:
        print("Result: NO discontinuities detected")
    else:
        print(
            f"WARNING: {len(outliers)} discontinuities at: "
            + ", ".join(str(s) for s in outliers[:20])
        )

    # --- FFT analysis ---
    N = len(data)
    data_ac = data.astype(np.float64) - np.mean(data)
    window = np.blackman(N)
    coherent_gain = np.sum(window) / N
    data_windowed = data_ac * window / coherent_gain

    fft_result = np.fft.rfft(data_windowed)
    fft_magnitude = np.abs(fft_result) * 2.0 / N
    fft_magnitude[0] /= 2.0

    freq_axis = np.fft.rfftfreq(N, d=1.0 / adc_sample_rate)

    fund_bin = np.argmax(fft_magnitude[1:]) + 1
    fund_freq = freq_axis[fund_bin]
    fund_amplitude = fft_magnitude[fund_bin]

    adc_fullscale = 8192.0
    fft_dbfs = 20 * np.log10(fft_magnitude / adc_fullscale + 1e-20)
    fund_dbfs = fft_dbfs[fund_bin]

    exclude_half_width = max(10, N // 10000)
    fft_for_sfdr = fft_magnitude.copy()
    fft_for_sfdr[
        max(1, fund_bin - exclude_half_width) : fund_bin + exclude_half_width + 1
    ] = 0
    fft_for_sfdr[0] = 0
    spur_bin = np.argmax(fft_for_sfdr)
    spur_amplitude = fft_for_sfdr[spur_bin]
    spur_freq = freq_axis[spur_bin]
    sfdr_db = 20 * np.log10(fund_amplitude / (spur_amplitude + 1e-20))

    signal_power = fund_amplitude ** 2
    noise_magnitude = fft_magnitude.copy()
    noise_magnitude[
        max(1, fund_bin - exclude_half_width) : fund_bin + exclude_half_width + 1
    ] = 0
    noise_magnitude[0] = 0
    noise_power = np.sum(noise_magnitude ** 2)
    snr_db = 10 * np.log10(signal_power / (noise_power + 1e-20))

    print(f"\n--- FFT Analysis ---")
    print(
        f"Fundamental: {fund_freq / 1e6:.6f} MHz (expected {actual_sine_freq / 1e6:.6f} MHz)"
    )
    print(f"  Amplitude: {fund_amplitude:.1f} codes ({fund_dbfs:.1f} dBFS)")
    print(f"  SFDR: {sfdr_db:.1f} dB, SNR: {snr_db:.1f} dB")

    if len(outliers) == 0 and sfdr_db > 40:
        print(
            f"\nPASS: No discontinuities, SFDR = {sfdr_db:.1f} dB. "
            f"DMA buffer ({buffer_samples:,} samples) is contiguous and uncorrupted."
        )
    elif len(outliers) == 0 and sfdr_db > 20:
        print(f"\nMARGINAL: No discontinuities, but SFDR = {sfdr_db:.1f} dB is low.")
    else:
        print(f"\nFAIL: {len(outliers)} discontinuities, SFDR = {sfdr_db:.1f} dB.")

    # --- FFT Plot: timing diagram + 2x2 data panels ---
    trigger_on_us = CH0_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    trigger_off_us = CH0_OFF_RAW * TDD_CLOCK_PERIOD_NS / 1000
    gate_on_us = CH1_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    gate_off_us = CH1_OFF_RAW * TDD_CLOCK_PERIOD_NS / 1000
    frame_period_ms_fft = TDD_FRAME_PERIOD_US / 1000
    gate_off_ms = gate_off_us / 1000

    fig = plt.figure(figsize=(14, 12))
    gs_main = gridspec.GridSpec(
        3, 1, figure=fig, height_ratios=[1.2, 2, 2], hspace=0.35
    )

    # Panel 1: TDD Timing Diagram (broken axis)
    gs_timing = gs_main[0].subgridspec(1, 2, width_ratios=[3, 2], wspace=0.08)
    ax_tl = fig.add_subplot(gs_timing[0])
    ax_tr = fig.add_subplot(gs_timing[1])

    sig_colors = {
        "Frame": "#2ca02c",
        "Laser Trigger (Ch0)": "#ff7f0e",
        "DMA Gate (Ch1)": "#9467bd",
    }
    sig_y = {"Frame": 2, "Laser Trigger (Ch0)": 1, "DMA Gate (Ch1)": 0}

    t_left_min, t_left_max = -2, max(gate_on_us * 1.5, 20)
    t_right_margin_ms = max(frame_period_ms_fft * 0.1, 5)
    t_right_min_ms = frame_period_ms_fft - t_right_margin_ms
    t_right_max_ms = frame_period_ms_fft + t_right_margin_ms * 0.3

    for label, y in sig_y.items():
        color = sig_colors[label]

        if label == "Frame":
            edges_t = [t_left_min, 0, 0, t_left_max]
            edges_v = [y, y, y + 0.7, y + 0.7]
        elif label == "Laser Trigger (Ch0)":
            edges_t = [
                t_left_min,
                trigger_on_us,
                trigger_on_us,
                trigger_off_us,
                trigger_off_us,
                t_left_max,
            ]
            edges_v = [y, y, y + 0.7, y + 0.7, y, y]
        else:
            edges_t = [t_left_min, gate_on_us, gate_on_us, t_left_max]
            edges_v = [y, y, y + 0.7, y + 0.7]
        ax_tl.plot(edges_t, edges_v, color=color, linewidth=2.0)
        ax_tl.plot(
            [t_left_min, t_left_max], [y, y], color=color, linewidth=0.5, alpha=0.3
        )
        ax_tl.text(
            t_left_min - 0.3,
            y + 0.35,
            label,
            ha="right",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=color,
        )

        if label == "Frame":
            edges_t_ms = [
                t_right_min_ms,
                frame_period_ms_fft,
                frame_period_ms_fft,
                t_right_max_ms,
            ]
            edges_v_r = [y + 0.7, y + 0.7, y, y]
        elif label == "Laser Trigger (Ch0)":  # already low at this timescale
            edges_t_ms = [t_right_min_ms, t_right_max_ms]
            edges_v_r = [y, y]
        else:
            edges_t_ms = [t_right_min_ms, gate_off_ms, gate_off_ms, t_right_max_ms]
            edges_v_r = [y + 0.7, y + 0.7, y, y]
        ax_tr.plot(edges_t_ms, edges_v_r, color=color, linewidth=2.0)
        ax_tr.plot(
            [t_right_min_ms, t_right_max_ms],
            [y, y],
            color=color,
            linewidth=0.5,
            alpha=0.3,
        )

    for t_val, t_label in [
        (0, "t=0"),
        (trigger_on_us, f"{trigger_on_us:.1f} \u00b5s"),
        (trigger_off_us, f"{trigger_off_us:.1f} \u00b5s"),
        (gate_on_us, f"{gate_on_us:.0f} \u00b5s"),
    ]:
        ax_tl.axvline(x=t_val, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
        ax_tl.text(
            t_val, -0.4, t_label, ha="center", va="top", fontsize=7, color="gray"
        )

    arrow_y = 3.0
    for t1, t2, desc in [
        (0, trigger_on_us, f"{trigger_on_us:.1f} \u00b5s"),
        (trigger_on_us, gate_on_us, f"{gate_on_us - trigger_on_us:.1f} \u00b5s"),
    ]:
        mid = (t1 + t2) / 2
        ax_tl.annotate(
            "",
            xy=(t2, arrow_y),
            xytext=(t1, arrow_y),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
        )
        ax_tl.text(mid, arrow_y + 0.15, desc, ha="center", va="bottom", fontsize=7)

    for t_val_ms, t_label in [
        (gate_off_ms, f"{gate_off_ms:.1f} ms"),
        (frame_period_ms_fft, f"{frame_period_ms_fft:.1f} ms"),
    ]:
        ax_tr.axvline(x=t_val_ms, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
        ax_tr.text(
            t_val_ms, -0.4, t_label, ha="center", va="top", fontsize=7, color="gray"
        )

    ax_tl.set_xlim(t_left_min, t_left_max)
    ax_tl.set_ylim(-0.8, 3.7)
    ax_tl.set_xlabel("Time (\u00b5s)", fontsize=9)
    ax_tl.set_yticks([])
    for spine in ["left", "top", "right"]:
        ax_tl.spines[spine].set_visible(False)

    ax_tr.set_xlim(t_right_min_ms, t_right_max_ms)
    ax_tr.set_ylim(-0.8, 3.7)
    ax_tr.set_xlabel("Time (ms)", fontsize=9)
    ax_tr.set_yticks([])
    for spine in ["left", "top", "right"]:
        ax_tr.spines[spine].set_visible(False)

    d = 0.015
    for ax_break, side in [(ax_tl, "right"), (ax_tr, "left")]:
        x_pos = 1.0 if side == "right" else 0.0
        for y_off in [-d, d]:
            ax_break.plot(
                [x_pos - d, x_pos + d],
                [0.5 + y_off - d, 0.5 + y_off + d],
                transform=ax_break.transAxes,
                color="gray",
                clip_on=False,
                linewidth=1,
            )

    fig.text(
        0.5,
        0.96,
        "TDD Timing: Frame \u2192 Laser Trigger (Ch0) \u2192 DMA Gate (Ch1)",
        ha="center",
        fontsize=11,
        fontweight="bold",
    )

    # Panel 2: Time-domain (full + zoomed)
    gs_data = gs_main[1].subgridspec(1, 2, wspace=0.3)
    ax_time_full = fig.add_subplot(gs_data[0])
    ax_time_zoom = fig.add_subplot(gs_data[1])

    ax_time_full.plot(time_ms, data, "b-", linewidth=0.3)
    ax_time_full.set_xlabel("Time (ms)")
    ax_time_full.set_ylabel("ADC Codes (inverted)")
    ax_time_full.set_title(f"Full Capture: {N:,} samples ({time_ms[-1]:.1f} ms)")
    ax_time_full.grid(True, alpha=0.3)

    samples_per_sine_cycle = adc_sample_rate / actual_sine_freq
    zoom_n = min(int(samples_per_sine_cycle * 10), N)
    time_us_zoom = np.arange(zoom_n) / adc_sample_rate * 1e6
    ax_time_zoom.plot(time_us_zoom, data[:zoom_n], "b.-", linewidth=0.8, markersize=1)
    ax_time_zoom.set_xlabel("Time (\u00b5s)")
    ax_time_zoom.set_ylabel("ADC Codes (inverted)")
    ax_time_zoom.set_title(f"Zoomed: 10 cycles of {actual_sine_freq / 1e6:.3f} MHz")
    ax_time_zoom.grid(True, alpha=0.3)

    # Panel 3: FFT (full + zoomed)
    gs_fft = gs_main[2].subgridspec(1, 2, wspace=0.3)
    ax_fft_full = fig.add_subplot(gs_fft[0])
    ax_fft_zoom = fig.add_subplot(gs_fft[1])

    freq_mhz = freq_axis / 1e6
    ax_fft_full.plot(freq_mhz, fft_dbfs, "b-", linewidth=0.5)
    ax_fft_full.axvline(x=fund_freq / 1e6, color="r", linestyle="--", alpha=0.5)
    ax_fft_full.set_xlabel("Frequency (MHz)")
    ax_fft_full.set_ylabel("Magnitude (dBFS)")
    ax_fft_full.set_title(
        f"FFT: {fund_freq / 1e6:.3f} MHz, "
        f"SFDR = {sfdr_db:.1f} dB, SNR = {snr_db:.1f} dB"
    )
    ax_fft_full.set_ylim(bottom=max(fft_dbfs.min(), -140))
    ax_fft_full.grid(True, alpha=0.3)

    zoom_bw = max(actual_sine_freq * 5, 5e6)
    zoom_mask = freq_axis <= zoom_bw
    ax_fft_zoom.plot(freq_mhz[zoom_mask], fft_dbfs[zoom_mask], "b-", linewidth=0.8)
    ax_fft_zoom.axvline(x=fund_freq / 1e6, color="r", linestyle="--", alpha=0.7)
    if spur_freq <= zoom_bw:
        ax_fft_zoom.plot(
            spur_freq / 1e6,
            fft_dbfs[spur_bin],
            "rv",
            markersize=8,
            label=f"Spur: {spur_freq / 1e6:.3f} MHz",
        )
        ax_fft_zoom.legend(fontsize=8)
    ax_fft_zoom.set_xlabel("Frequency (MHz)")
    ax_fft_zoom.set_ylabel("Magnitude (dBFS)")
    ax_fft_zoom.set_title(f"Zoomed FFT (0 \u2013 {zoom_bw / 1e6:.0f} MHz)")
    ax_fft_zoom.grid(True, alpha=0.3)

    fig.subplots_adjust(top=0.93)

elif mode == "single":
    # Detect pulses
    pulse_threshold = 2000
    pulse_mask = data > pulse_threshold
    pulses = []

    if np.any(pulse_mask):
        pulse_indices = np.where(pulse_mask)[0]
        start = pulse_indices[0]
        for i in range(1, len(pulse_indices)):
            if pulse_indices[i] - pulse_indices[i - 1] > 100:
                pulses.append((start, pulse_indices[i - 1]))
                start = pulse_indices[i]
        pulses.append((start, pulse_indices[-1]))
        print(f"Detected {len(pulses)} pulse(s)")
    else:
        print("No pulses detected")

    dma_sync_on_us = CH1_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    dma_sync_off_us = CH1_OFF_RAW * TDD_CLOCK_PERIOD_NS / 1000
    laser_trigger_on_us = CH0_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    laser_trigger_off_us = CH0_OFF_RAW * TDD_CLOCK_PERIOD_NS / 1000
    frame_period_ms = TDD_FRAME_PERIOD_US / 1000
    dma_sync_on_ms = dma_sync_on_us / 1000
    dma_sync_off_ms = dma_sync_off_us / 1000
    laser_trigger_ms = laser_trigger_on_us / 1000

    fig = plt.figure(figsize=(14, 11))
    gs_main = gridspec.GridSpec(
        3, 1, figure=fig, height_ratios=[1.5, 2, 2], hspace=0.35
    )
    gs_timing = gs_main[0].subgridspec(1, 2, width_ratios=[3, 2], wspace=0.08)
    ax_tl = fig.add_subplot(gs_timing[0])
    ax_tr = fig.add_subplot(gs_timing[1])
    ax_full = fig.add_subplot(gs_main[1])
    ax_zoom = fig.add_subplot(gs_main[2])

    # Panel 1: TDD Timing Diagram (broken axis)
    sig_colors = {
        "Frame": "#2ca02c",
        "DMA Sync (Ch1)": "#9467bd",
        "Laser Trigger (Ch0)": "#ff7f0e",
    }
    sig_y = {"Frame": 2, "DMA Sync (Ch1)": 1, "Laser Trigger (Ch0)": 0}

    t_left_min, t_left_max = -2, max(laser_trigger_off_us * 1.5, 20)
    t_right_margin_ms = max(frame_period_ms * 0.1, 5)
    t_right_min_ms = frame_period_ms - t_right_margin_ms
    t_right_max_ms = frame_period_ms + t_right_margin_ms * 0.3

    for label, y in sig_y.items():
        color = sig_colors[label]

        if label == "Frame":
            edges_t = [t_left_min, 0, 0, t_left_max]
            edges_v = [y, y, y + 0.7, y + 0.7]
        elif label == "DMA Sync (Ch1)":
            edges_t = [t_left_min, dma_sync_on_us, dma_sync_on_us, t_left_max]
            edges_v = [y, y, y + 0.7, y + 0.7]
        else:
            edges_t = [
                t_left_min,
                laser_trigger_on_us,
                laser_trigger_on_us,
                laser_trigger_off_us,
                laser_trigger_off_us,
                t_left_max,
            ]
            edges_v = [y, y, y + 0.7, y + 0.7, y, y]
        ax_tl.plot(edges_t, edges_v, color=color, linewidth=2.0)
        ax_tl.plot(
            [t_left_min, t_left_max], [y, y], color=color, linewidth=0.5, alpha=0.3
        )
        ax_tl.text(
            t_left_min - 0.3,
            y + 0.35,
            label,
            ha="right",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=color,
        )

        if label == "Frame":
            edges_t_ms = [
                t_right_min_ms,
                frame_period_ms,
                frame_period_ms,
                t_right_max_ms,
            ]
            edges_v_r = [y + 0.7, y + 0.7, y, y]
        elif label == "DMA Sync (Ch1)":
            edges_t_ms = [
                t_right_min_ms,
                dma_sync_off_ms,
                dma_sync_off_ms,
                t_right_max_ms,
            ]
            edges_v_r = [y + 0.7, y + 0.7, y, y]
        else:
            edges_t_ms = [t_right_min_ms, t_right_max_ms]
            edges_v_r = [y, y]
        ax_tr.plot(edges_t_ms, edges_v_r, color=color, linewidth=2.0)
        ax_tr.plot(
            [t_right_min_ms, t_right_max_ms],
            [y, y],
            color=color,
            linewidth=0.5,
            alpha=0.3,
        )

    for t_val, t_label in [
        (0, "t=0"),
        (dma_sync_on_us, f"{dma_sync_on_us:.0f} \u00b5s"),
        (laser_trigger_on_us, f"{laser_trigger_on_us:.0f} \u00b5s"),
        (laser_trigger_off_us, f"{laser_trigger_off_us:.0f} \u00b5s"),
    ]:
        ax_tl.axvline(x=t_val, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
        ax_tl.text(
            t_val, -0.4, t_label, ha="center", va="top", fontsize=7, color="gray"
        )

    arrow_y = 3.0
    for t1, t2, desc in [
        (0, dma_sync_on_us, f"{dma_sync_on_us:.0f} \u00b5s"),
        (
            dma_sync_on_us,
            laser_trigger_on_us,
            f"{laser_trigger_on_us - dma_sync_on_us:.0f} \u00b5s",
        ),
    ]:
        mid = (t1 + t2) / 2
        ax_tl.annotate(
            "",
            xy=(t2, arrow_y),
            xytext=(t1, arrow_y),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
        )
        ax_tl.text(mid, arrow_y + 0.15, desc, ha="center", va="bottom", fontsize=7)

    for t_val_ms, t_label in [
        (dma_sync_off_ms, f"{dma_sync_off_ms:.1f} ms"),
        (frame_period_ms, f"{frame_period_ms:.1f} ms"),
    ]:
        ax_tr.axvline(x=t_val_ms, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
        ax_tr.text(
            t_val_ms, -0.4, t_label, ha="center", va="top", fontsize=7, color="gray"
        )

    ax_tl.set_xlim(t_left_min, t_left_max)
    ax_tl.set_ylim(-0.8, 3.7)
    ax_tl.set_xlabel("Time (\u00b5s)", fontsize=9)
    ax_tl.set_yticks([])
    for spine in ["left", "top", "right"]:
        ax_tl.spines[spine].set_visible(False)

    ax_tr.set_xlim(t_right_min_ms, t_right_max_ms)
    ax_tr.set_ylim(-0.8, 3.7)
    ax_tr.set_xlabel("Time (ms)", fontsize=9)
    ax_tr.set_yticks([])
    for spine in ["left", "top", "right"]:
        ax_tr.spines[spine].set_visible(False)

    d = 0.015
    for ax_break, side in [(ax_tl, "right"), (ax_tr, "left")]:
        x_pos = 1.0 if side == "right" else 0.0
        for y_off in [-d, d]:
            ax_break.plot(
                [x_pos - d, x_pos + d],
                [0.5 + y_off - d, 0.5 + y_off + d],
                transform=ax_break.transAxes,
                color="gray",
                clip_on=False,
                linewidth=1,
            )

    fig.text(
        0.5,
        0.96,
        "TDD Timing: Frame \u2192 DMA Sync (Ch1) \u2192 Laser Trigger (Ch0)",
        ha="center",
        fontsize=11,
        fontweight="bold",
    )

    # Panel 2: Full ADC Capture
    ax_full.plot(time_ms, data, "b-", linewidth=0.5)
    ax_full.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
    ax_full.axvspan(dma_sync_on_ms, dma_sync_off_ms, alpha=0.06, color="#9467bd")
    ax_full.axvline(x=0, color="#2ca02c", linewidth=2, alpha=0.8)
    ax_full.axvline(
        x=frame_period_ms, color="#2ca02c", linewidth=2, alpha=0.8, linestyle="--"
    )
    ax_full.axvline(x=dma_sync_on_ms, color="#9467bd", linewidth=2, alpha=0.8)
    ax_full.axvline(
        x=dma_sync_off_ms, color="#9467bd", linewidth=2, alpha=0.8, linestyle="--"
    )
    ax_full.axvline(x=laser_trigger_ms, color="#ff7f0e", linewidth=2, alpha=0.8)
    ax_full.axvspan(dma_sync_off_ms, frame_period_ms + 2, alpha=0.1, color="gray")
    ax_full.set_xlim(-1, frame_period_ms + 2)
    ax_full.set_xlabel("Time (ms)", fontsize=9)
    ax_full.set_ylabel("ADC Code (inverted)", fontsize=9)
    ax_full.set_title(
        f"Full Capture: {buffer_samples:,} samples "
        f"({time_us[-1] / 1000:.1f} ms) | "
        f"Target: {target_distance_m:.0f} m "
        f"(echo delay: {echo_delay_us:.2f} \u00b5s)",
        fontsize=10,
        fontweight="bold",
    )
    ax_full.grid(True, alpha=0.3)
    ax_full.legend(
        handles=[
            Line2D([0], [0], color="#2ca02c", lw=2, label="Frame (start / end)"),
            Line2D(
                [0],
                [0],
                color="#9467bd",
                lw=2,
                label=f"DMA Sync Ch1 ON ({dma_sync_on_ms:.1f} ms)",
            ),
            Line2D(
                [0],
                [0],
                color="#9467bd",
                lw=2,
                linestyle="--",
                label=f"DMA Sync Ch1 OFF ({dma_sync_off_ms:.1f} ms)",
            ),
            Line2D(
                [0],
                [0],
                color="#ff7f0e",
                lw=2,
                label=f"Laser Trigger Ch0 ({laser_trigger_ms:.1f} ms)",
            ),
        ],
        loc="lower left",
        fontsize=8,
        ncol=2,
        framealpha=0.9,
    )

    # Panel 3: Zoomed Echo
    if len(pulses) > 0:
        pulse_center = (pulses[0][0] + pulses[0][1]) // 2
        pulse_start_us = time_us[pulses[0][0]]
        pulse_end_us = time_us[pulses[0][1]]
        pulse_width_detected = pulse_end_us - pulse_start_us
        zoom_half = max(int(pulse_width_detected * 3 * adc_sample_rate / 1e6), 5000)
        zoom_start = max(0, pulse_center - zoom_half)
        zoom_end = min(len(data), pulse_center + zoom_half)
        ax_zoom.plot(
            time_us[zoom_start:zoom_end], data[zoom_start:zoom_end], "b-", linewidth=1.0
        )
        ax_zoom.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
        ax_zoom.axvspan(pulse_start_us, pulse_end_us, alpha=0.12, color="#ff7f0e")

        measured_delay_us = pulse_start_us - laser_trigger_on_us
        measured_dist_m = measured_delay_us * 1e-6 * SPEED_OF_LIGHT / 2
        ax_zoom.annotate(
            f"Echo: {pulse_width_detected:.0f} \u00b5s wide\n"
            f"Delay: {measured_delay_us:.1f} \u00b5s\n"
            f"\u2248 {measured_dist_m:.1f} m",
            xy=(pulse_start_us, data[pulses[0][0]]),
            xytext=(
                pulse_start_us - (zoom_half / adc_sample_rate * 1e6) * 0.5,
                max(data[zoom_start:zoom_end]) * 0.75,
            ),
            fontsize=9,
            color="#d62728",
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="white",
                alpha=0.9,
                edgecolor="#d62728",
            ),
            arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
        )
        ax_zoom.set_title(
            f"Echo Detail ({pulse_start_us / 1000:.2f} ms from DMA start)",
            fontsize=10,
            fontweight="bold",
        )
    else:
        zoom_samples = int(1000 * adc_sample_rate / 1e6)
        ax_zoom.plot(time_us[:zoom_samples], data[:zoom_samples], "b-", linewidth=1.0)
        ax_zoom.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
        ax_zoom.set_title(
            "First 1 ms (no echo detected)", fontsize=10, fontweight="bold"
        )
    ax_zoom.set_xlabel("Time (\u00b5s)", fontsize=9)
    ax_zoom.set_ylabel("ADC Code (inverted)", fontsize=9)
    ax_zoom.grid(True, alpha=0.3)

    fig.subplots_adjust(top=0.93)

else:
    # Multi-pulse mode
    # Detect pulses
    pulse_threshold = 2000
    pulse_mask = data > pulse_threshold
    pulses = []

    if np.any(pulse_mask):
        pulse_indices = np.where(pulse_mask)[0]
        start = pulse_indices[0]
        for i in range(1, len(pulse_indices)):
            if pulse_indices[i] - pulse_indices[i - 1] > 100:
                pulses.append((start, pulse_indices[i - 1]))
                start = pulse_indices[i]
        pulses.append((start, pulse_indices[-1]))
        print(f"Detected {len(pulses)} pulse(s)")

        if len(pulses) >= 2:
            times = [p[0] / adc_sample_rate * 1e6 for p in pulses]
            spacings = [times[i + 1] - times[i] for i in range(len(times) - 1)]
            print(
                f"Pulse spacing: {np.mean(spacings):.1f} us "
                f"(expected: {TDD_FRAME_PERIOD_US:.0f} us)"
            )
    else:
        print("No pulses detected")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    trigger_on_us = CH0_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    dma_sync_on_us = CH1_ON_RAW * TDD_CLOCK_PERIOD_NS / 1000
    dma_sync_off_us = CH1_OFF_RAW * TDD_CLOCK_PERIOD_NS / 1000

    ax1.plot(time_us, data, "b-", linewidth=0.5)
    ax1.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
    for i, (ps, pe) in enumerate(pulses):
        ax1.axvspan(time_us[ps], time_us[pe], alpha=0.15, color="#d62728")
        if i == 0:
            ax1.axvspan(
                time_us[ps],
                time_us[pe],
                alpha=0,
                color="#d62728",
                label="Captured pulse",
            )
    ax1.set_xlabel("Time (\u00b5s)")
    ax1.set_ylabel("ADC Code (inverted)")
    ax1.set_title(
        f"ADA4356 LiDAR - Multi-Pulse "
        f"(Target: {target_distance_m} m, Frame: {TDD_FRAME_PERIOD_US:.0f} \u00b5s)"
    )
    ax1.grid(True, alpha=0.3)
    if pulses:
        ax1.legend(fontsize=8, loc="upper right")

    zoom_us = 150.0
    zoom_samples = int(zoom_us * adc_sample_rate / 1e6)
    ax2.plot(time_us[:zoom_samples], data[:zoom_samples], "b-", linewidth=1.0)
    ax2.axhline(y=0, color="gray", linestyle="-", alpha=0.3)

    for frame_num in range(int(zoom_us / TDD_FRAME_PERIOD_US) + 1):
        frame_time = frame_num * TDD_FRAME_PERIOD_US
        # DMA sync (Ch1) shaded region
        sync_on = frame_time + dma_sync_on_us
        sync_off = frame_time + dma_sync_off_us
        if sync_on < zoom_us:
            ax2.axvspan(sync_on, min(sync_off, zoom_us), alpha=0.08, color="#9467bd")
        # Frame start
        if frame_time <= zoom_us:
            ax2.axvline(
                x=frame_time, color="#2ca02c", linestyle="-", alpha=0.4, linewidth=2
            )
        # Laser trigger (Ch0)
        trigger_time = frame_time + trigger_on_us
        if trigger_time < zoom_us:
            ax2.axvline(x=trigger_time, color="#ff7f0e", linestyle="--", alpha=0.7)

    # Highlight captured pulses and annotate M2K latency
    m2k_latency_us = None
    for ps, pe in pulses:
        if time_us[ps] < zoom_us:
            ax2.axvspan(
                time_us[ps], min(time_us[pe], zoom_us), alpha=0.15, color="#d62728"
            )
    if len(pulses) > 0:
        first_pulse_us = time_us[pulses[0][0]]
        expected_echo_us = trigger_on_us + echo_delay_us
        m2k_latency_us = first_pulse_us - expected_echo_us
        ax2.annotate(
            f"M2K latency: {m2k_latency_us:.1f} \u00b5s\n"
            f"(trigger \u2192 analog out)",
            xy=(first_pulse_us, data[pulses[0][0]]),
            xytext=(first_pulse_us + 10, max(data[:zoom_samples]) * 0.6),
            fontsize=7,
            color="#555555",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="lightyellow",
                edgecolor="gray",
                alpha=0.9,
            ),
            arrowprops=dict(arrowstyle="->", color="gray", lw=1.0),
        )

    legend_handles = [
        Line2D([0], [0], color="#2ca02c", lw=2, label="Frame start"),
        Line2D(
            [0],
            [0],
            color="#ff7f0e",
            lw=2,
            linestyle="--",
            label=f"laser_trigger Ch0 ({trigger_on_us:.0f} \u00b5s)",
        ),
        Line2D(
            [0],
            [0],
            color="#9467bd",
            lw=8,
            alpha=0.3,
            label=f"dma_sync Ch1 ({dma_sync_on_us:.0f}\u2013{dma_sync_off_us:.0f} \u00b5s)",
        ),
        Line2D([0], [0], color="#d62728", lw=8, alpha=0.3, label="Captured pulse"),
    ]
    if m2k_latency_us is not None:
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="none",
                label=f"M2K latency: {m2k_latency_us:.1f} \u00b5s",
            )
        )
    ax2.legend(handles=legend_handles, fontsize=7, loc="upper right", framealpha=0.9)
    ax2.set_xlabel("Time (\u00b5s)")
    ax2.set_ylabel("ADC Code (inverted)")
    ax2.set_title(
        f"Zoomed: Frame \u2192 dma_sync (Ch1) \u2192 laser_trigger (Ch0) "
        f"\u2192 Captured pulse"
    )
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

plt.savefig("/tmp/lidar_simulation.png", dpi=150)
print(f"Plot saved: /tmp/lidar_simulation.png")

# Cleanup
aout.stop()
libm2k.contextClose(m2k)
lidar.rx_destroy_buffer()
print("Done!")
