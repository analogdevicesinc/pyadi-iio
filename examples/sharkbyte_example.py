# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
#
# Sharkbyte dual-ADC example with resolution configuration

import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import adi

# Configuration
resolution = 8  # Options: 8, 12, or 14 bits
run_until_drift = False  # True: run until drift > 10, False: run fixed 100 iterations

my_uri = "ip:192.168.2.1" if len(sys.argv) == 1 else sys.argv[1]

print(f"Connecting to {my_uri}...")
print(f"Resolution: {resolution}-bit")

# Create SSH connection for direct register access
ssh = adi.sshfs(address=my_uri, username="root", password="analog")

# Read AXI HMCAD15XX CLK_FREQ register (0x54)
hmcad_base_addr = 0x44A00000
reg_offset = 0x54
full_addr = hmcad_base_addr + reg_offset

stdout, stderr = ssh._run(f"busybox devmem 0x{full_addr:08X} 32")
print(f"\nReading HMCAD15XX CLK_FREQ register 0x54 (address 0x{full_addr:08X}):")
print(f"Raw value: {stdout.strip()}")

# Decode unsigned 16.16 fixed-point format
if stdout.strip():
    raw_value = int(stdout.strip(), 16)
    # Upper 16 bits = integer part, lower 16 bits = fractional part
    clk_freq_ratio = raw_value / 65536.0  # Convert from 16.16 format

    # Assuming 100MHz processor clock
    processor_clock = 100e6  # 100 MHz
    interface_clock = clk_freq_ratio * processor_clock

    print(f"CLK_FREQ ratio: {clk_freq_ratio:.6f}")
    print(f"Interface clock: {interface_clock/1e6:.6f} MHz (assuming 100MHz processor clock)")
    print(f"Note: Actual sampling clock = Interface clock * CLK_RATIO")

if stderr:
    print(f"Error: {stderr}")

# Write to Data Offload Control Registers
print("\n" + "="*80)
print("DATA OFFLOAD CONTROL REGISTER WRITE")
print("="*80)

# First data offload (0x44B00000)
offload1_base = 0x44B00000
offload1_addr = offload1_base + 0x88
stdout, stderr = ssh._run(f"busybox devmem 0x{offload1_addr:08X} 32 0x2")
print(f"Offload 1 - Writing 0x2 to register 0x88 (address 0x{offload1_addr:08X})")
if stderr:
    print(f"  Error: {stderr}")
else:
    print(f"  Success")

# Second data offload (0x44B10000)
offload2_base = 0x44B10000
offload2_addr = offload2_base + 0x88
stdout, stderr = ssh._run(f"busybox devmem 0x{offload2_addr:08X} 32 0x2")
print(f"Offload 2 - Writing 0x2 to register 0x88 (address 0x{offload2_addr:08X})")
if stderr:
    print(f"  Error: {stderr}")
else:
    print(f"  Success")

print("="*80)

# Create sharkbyte multi-ADC manager with TDD synchronization
multi = adi.sharkbyte(uri=my_uri,
                      device1_name="axi_adc1_hmcad15xx",
                      device2_name="axi_adc2_hmcad15xx",
                      enable_tddn=True)

# Configure TDD for DMA synchronization
multi.tddn.enable = 0

tddn_channel_on_raw   =  0
tddn_channel_off_raw  =  10
tddn_channel_polarity =  0
tddn_channel_enable   =  1

multi.tddn.burst_count = 1
multi.tddn.startup_delay_ms = 0
multi.tddn.frame_length_ms  = 0.1
multi.tddn.sync_internal=1
multi.tddn.sync_external=0



multi.tddn.channel[0].on_ms    = 0
multi.tddn.channel[0].off_ms   = 0
multi.tddn.channel[0].polarity = 0
multi.tddn.channel[0].enable   = 1

multi.tddn.channel[1].on_ms    = 0
multi.tddn.channel[1].off_ms   = 0
multi.tddn.channel[1].polarity = 0
multi.tddn.channel[1].enable   = 1

multi.tddn.enable = 1
multi.tddn.enable = 0

# ADC1 DMA sync
multi.tddn.channel[0].on_raw   = tddn_channel_on_raw
multi.tddn.channel[0].off_raw  = tddn_channel_off_raw
multi.tddn.channel[0].polarity = tddn_channel_polarity
multi.tddn.channel[0].enable   = tddn_channel_enable

# ADC2 DMA sync
multi.tddn.channel[1].on_raw   = tddn_channel_on_raw
multi.tddn.channel[1].off_raw  = tddn_channel_off_raw
multi.tddn.channel[1].polarity = tddn_channel_polarity
multi.tddn.channel[1].enable   = tddn_channel_enable
multi.tddn.enable = 1

# Configure based on resolution
if resolution in [8, 12]:
    # Single channel mode, all inputs to IN4
    mode = "SINGLE_CHANNEL"
    num_channels = 1

    # Set input to IN4 for all channels
    for ch in multi.dev1.channel:
        ch.input_select = "IP4_IN4"
    for ch in multi.dev2.channel:
        ch.input_select = "IP4_IN4"

    multi.dev1.rx_enabled_channels = [0]
    multi.dev2.rx_enabled_channels = [0]

    print(f"Mode: {mode}")
    print(f"All inputs set to IP4_IN4")

elif resolution == 14:
    # Quad channel mode, each channel gets its own input
    mode = "QUAD_CHANNEL"
    num_channels = 4
    # Set each channel to its corresponding input
    input_map = ["IP1_IN1", "IP2_IN2", "IP3_IN3", "IP4_IN4"]
    for i, ch in enumerate(multi.dev1.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]
    for i, ch in enumerate(multi.dev2.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]

    multi.dev1.rx_enabled_channels = [0,1,2,3]
    multi.dev2.rx_enabled_channels = [0,1,2,3]

    print(f"Mode: {mode}")
    print(f"Channel inputs: {input_map}")

else:
    raise ValueError(f"Invalid resolution: {resolution}. Use 8, 12, or 14.")

# Configure buffer size
N_rx = 2**15
multi.dev1.rx_buffer_size = N_rx
multi.dev2.rx_buffer_size = N_rx

# Test pattern definitions
custom_pattern = 0x7FFF
fixed_test_pattern = 0x10
ramp_pattern = 0x40
pattern_disabled = 0x00

multi.dev1.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev2.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev1.hmcad15xx_register_write(0x25, pattern_disabled)
multi.dev2.hmcad15xx_register_write(0x25, pattern_disabled)

print(f"Buffer size: {N_rx} samples per channel")
print(f"Enabled channels: {num_channels}")

# Capture data - run until drift or fixed iterations
drift_threshold = 10
num_iterations = 100
fs = int(multi.dev1.sampling_rate)

if run_until_drift:
    print(f"\nCapturing iterations until drift > {drift_threshold} samples...")
else:
    print(f"\nCapturing {num_iterations} fixed iterations...")
print(f"Sampling rate: {fs/1e6:.2f} MSPS")

# Helper function for phase measurement
def compute_phase_xcorr(sig1, sig2, max_lag=100):
    """Compute phase difference using cross-correlation"""
    # Normalize
    sig1_norm = (sig1 - np.mean(sig1)) / (np.std(sig1) + 1e-10)
    sig2_norm = (sig2 - np.mean(sig2)) / (np.std(sig2) + 1e-10)

    # Compute correlation only in the region of interest
    best_lag = 0
    best_corr = -np.inf

    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            corr = np.sum(sig1_norm[:lag] * sig2_norm[-lag:])
        elif lag > 0:
            corr = np.sum(sig1_norm[lag:] * sig2_norm[:-lag])
        else:
            corr = np.sum(sig1_norm * sig2_norm)

        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    return -best_lag

# Storage for all iterations
all_data = []
phase_differences_start = []
phase_differences_end = []
phase_drift = []
peak_frequencies = []

iteration = 0
drift = 0
while True:
    # Check exit condition based on mode
    if run_until_drift:
        if iteration > 0 and abs(drift) > drift_threshold:
            break
    else:
        if iteration >= num_iterations:
            break

    iteration += 1
    print(f"Iteration {iteration}{'/' + str(num_iterations) if not run_until_drift else ''}...")
    multi.tddn.enable = 1
    data = multi.rx()
    all_data.append(data)

    # Extract data based on resolution
    if resolution == 14:
        signal1 = data[0][3]  # ADC1, channel 3
        signal2 = data[1][3]  # ADC2, channel 3
    else:
        signal1 = data[0]
        signal2 = data[1]

    # Measure phase at BEGINNING of buffer
    chunk_size = 8192
    sig1_start = signal1[:chunk_size]
    sig2_start = signal2[:chunk_size]
    phase_start = compute_phase_xcorr(sig1_start, sig2_start)

    # Measure phase at END of buffer
    sig1_end = signal1[-chunk_size:]
    sig2_end = signal2[-chunk_size:]
    phase_end = compute_phase_xcorr(sig1_end, sig2_end)

    # Calculate drift
    drift = phase_end - phase_start

    phase_differences_start.append(phase_start)
    phase_differences_end.append(phase_end)
    phase_drift.append(drift)

    # Find peak frequency for reference
    sig1_norm = (sig1_start - np.mean(sig1_start)) / (np.std(sig1_start) + 1e-10)
    fft1 = np.fft.fft(sig1_norm)
    fft_mag1 = np.abs(fft1)
    fft_freq = np.fft.fftfreq(len(sig1_norm), 1/fs)
    positive_freq_idx = fft_freq > 0
    peak_idx = np.argmax(fft_mag1[positive_freq_idx])
    positive_freqs = np.where(fft_freq > 0)[0]
    peak_freq = fft_freq[positive_freqs[peak_idx]]
    peak_frequencies.append(peak_freq)

    print(f"  Phase @ start: {phase_start:7.3f} samples")
    print(f"  Phase @ end:   {phase_end:7.3f} samples")
    print(f"  Drift:         {drift:7.3f} samples, Peak freq: {peak_freq/1e6:.4f} MHz")

    multi.dev1.rx_destroy_buffer()
    multi.dev2.rx_destroy_buffer()
    multi.tddn.enable = 0

    # Check if drift exceeded threshold (for loop exit message)
    if run_until_drift and abs(drift) > drift_threshold:
        print(f"\n*** Drift threshold exceeded! |{drift:.3f}| > {drift_threshold} samples ***")

# Find iteration with maximum drift
max_drift_idx = np.argmax(np.abs(phase_drift))
max_phase_diff_start = phase_differences_start[max_drift_idx]
max_phase_diff_end = phase_differences_end[max_drift_idx]
max_drift = phase_drift[max_drift_idx]

print("\n" + "="*80)
if run_until_drift:
    print(f"Completed {iteration} iterations (stopped when |drift| > {drift_threshold})")
else:
    print(f"Completed {iteration} fixed iterations")
print(f"Phase Difference Statistics (in samples):")
print(f"\n  At Buffer Start:")
print(f"    Mean: {np.mean(phase_differences_start):7.3f} samples")
print(f"    Std:  {np.std(phase_differences_start):7.3f} samples")
print(f"    Min:  {np.min(phase_differences_start):7.3f} samples")
print(f"    Max:  {np.max(phase_differences_start):7.3f} samples")

print(f"\n  At Buffer End:")
print(f"    Mean: {np.mean(phase_differences_end):7.3f} samples")
print(f"    Std:  {np.std(phase_differences_end):7.3f} samples")
print(f"    Min:  {np.min(phase_differences_end):7.3f} samples")
print(f"    Max:  {np.max(phase_differences_end):7.3f} samples")

print(f"\n  Drift (End - Start):")
print(f"    Mean: {np.mean(phase_drift):7.3f} samples")
print(f"    Std:  {np.std(phase_drift):7.3f} samples")
print(f"    Min:  {np.min(phase_drift):7.3f} samples")
print(f"    Max:  {np.max(phase_drift):7.3f} samples")

print(f"\nPlotting iteration {max_drift_idx + 1} with maximum |phase| at start:")
print(f"  Start: {max_phase_diff_start:.3f} samples")
print(f"  End:   {max_phase_diff_end:.3f} samples")
print(f"  Drift: {max_drift:.3f} samples")
print("="*80)

# Use the data from iteration with maximum phase difference
data = all_data[max_drift_idx]

if resolution == 14:
    fft_data1 = data[0][3]  # ADC1, channel 3
    fft_data2 = data[1][3]  # ADC2, channel 3
else:
    fft_data1 = data[0]
    fft_data2 = data[1]

# Compute FFT for plotting
fft_result1 = np.fft.fft(fft_data1)
fft_freq1 = np.fft.fftfreq(len(fft_data1), 1/fs)
fft_mag1 = np.abs(fft_result1)
positive_freq_idx1 = fft_freq1 > 0
peak_idx1 = np.argmax(fft_mag1[positive_freq_idx1])
peak_freq1 = fft_freq1[positive_freq_idx1][peak_idx1]

fft_result2 = np.fft.fft(fft_data2)
fft_freq2 = np.fft.fftfreq(len(fft_data2), 1/fs)
fft_mag2 = np.abs(fft_result2)
positive_freq_idx2 = fft_freq2 > 0
peak_idx2 = np.argmax(fft_mag2[positive_freq_idx2])
peak_freq2 = fft_freq2[positive_freq_idx2][peak_idx2]

print(f"ADC1 Peak frequency: {peak_freq1/1e6:.4f} MHz")
print(f"ADC2 Peak frequency: {peak_freq2/1e6:.4f} MHz")
if resolution == 14:
    plt.plot(data[0][3],'o', label="ADC1 Channel 0")
    plt.plot(data[1][3],'o', label="ADC2 Channel 0")
else: 
    plt.plot(data[0],'o', label="ADC1 Channel 0")
    plt.plot(data[1],'o', label="ADC2 Channel 0")



plt.tight_layout()
plt.suptitle(f"Sharkbyte {resolution}-bit ADC Data - Iteration {max_drift_idx + 1}\n(Start: {max_phase_diff_start:.3f} samp, End: {max_phase_diff_end:.3f} samp, Drift: {max_drift:.3f} samp)", y=1.02)
plt.show()


multi.tddn.enable = 0


multi.tddn.channel[0].on_ms    = 0
multi.tddn.channel[0].off_ms   = 0
multi.tddn.channel[0].polarity = 0
multi.tddn.channel[0].enable   = 1


multi.tddn.channel[1].on_ms    = 0
multi.tddn.channel[1].off_ms   = 0
multi.tddn.channel[1].polarity = 0
multi.tddn.channel[1].enable   = 1


multi.tddn.enable = 1
multi.tddn.enable = 0

# Cleanup
multi.dev1.rx_destroy_buffer()
multi.dev2.rx_destroy_buffer()
print("Done")
