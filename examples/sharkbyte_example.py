# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg') # or 'Qt5Agg', 'QtAgg'
import numpy as np
from scipy import signal
import fft_analysis
from collections import namedtuple

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))

# Individual device access (for first plot demonstration)
hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")
ad5696_dev     = adi.ad5686(uri=my_uri)
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")

tddn_channel_on_raw = 0
tddn_channel_off_raw = 10
tddn_channel_polarity = 0
tddn_channel_enable = 1

tddn = adi.tddn(my_uri)
tddn.burst_count = 0
tddn.startup_delay_ms = 0
tddn.frame_length_ms  = 1

tddn.enable = 0

tddn.channel[0].on_ms    = 0
tddn.channel[0].off_ms   = 0
tddn.channel[0].polarity = 0
tddn.channel[0].enable   = 1

tddn.channel[1].on_ms    = 0
tddn.channel[1].off_ms   = 0
tddn.channel[1].polarity = 0
tddn.channel[1].enable   = 1

tddn.enable = 1
tddn.enable = 0

# ADC1 DMA sync
tddn.channel[0].on_raw   = tddn_channel_on_raw
tddn.channel[0].off_raw  = tddn_channel_off_raw
tddn.channel[0].polarity = tddn_channel_polarity
tddn.channel[0].enable   = tddn_channel_enable

# ADC2 DMA sync
tddn.channel[1].on_raw   = tddn_channel_on_raw
tddn.channel[1].off_raw  = tddn_channel_off_raw
tddn.channel[1].polarity = tddn_channel_polarity
tddn.channel[1].enable   = tddn_channel_enable

gpio_controller.gpio_clk_sel = 0

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

custom_pattern       = 0x7fff
fixed_test_pattern   = 0x10
ramp_pattern         = 0x40
pattern_disabled     = 0x00

hmcad15xx_dev1.rx_buffer_size = 2**18
hmcad15xx_dev2.rx_buffer_size = 2**18

hmcad15xx_dev1.rx_enabled_channels = [0]
hmcad15xx_dev2.rx_enabled_channels = [0]

print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))

hmcad15xx_dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev1.hmcad15xx_register_write(0x25, ramp_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x25, ramp_pattern)

#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3

hmcad15xx_dev1.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[1].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[2].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[3].input_select = "IP1_IN1"

hmcad15xx_dev2.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[1].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[2].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[3].input_select = "IP1_IN1"

# Enable TDD and configure sync for synchronized multi-ADC capture
tddn.enable = 1
tddn.sync_external = False

# Second demonstration: Synchronized multi-ADC capture using sharkbyte class
print("\n--- Synchronized Multi-ADC Capture ---")
multi = adi.sharkbyte(uri=my_uri,
                      device1_name="axi_adc1_hmcad15xx",
                      device2_name="axi_adc2_hmcad15xx",
                      tddn=tddn)

# Configure buffer size and enabled channels
multi.rx_buffer_size = 2**17
multi.rx_enabled_channels = [0]  # Apply to both devices

print("Multi-ADC rx_enabled_channels: " + str(multi.rx_enabled_channels))

# Configure individual device settings via dev1 and dev2 properties
multi.dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev1.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev2.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev1.hmcad15xx_register_write(0x25, pattern_disabled)
multi.dev2.hmcad15xx_register_write(0x25, pattern_disabled)

# Set input selections
multi.dev1.channel[0].input_select = "IP4_IN4"
multi.dev2.channel[0].input_select = "IP4_IN4"
multi.dev1.channel[1].input_select = "IP4_IN4"
multi.dev2.channel[1].input_select = "IP4_IN4"
multi.dev1.channel[2].input_select = "IP4_IN4"
multi.dev2.channel[2].input_select = "IP4_IN4"
multi.dev1.channel[3].input_select = "IP4_IN4"
multi.dev2.channel[3].input_select = "IP4_IN4"

# Perform synchronized capture
sync_data1, sync_data2 = multi.rx()

# Plot synchronized channel 0 from both devices
plt.figure(figsize=(12, 6))
plt.plot(sync_data1, label='hmcad15xx_dev1 - Channel 0 (Synced)', alpha=0.7)
plt.plot(sync_data2, label='hmcad15xx_dev2 - Channel 0 (Synced)', alpha=0.7)
plt.xlabel('Sample Index')
plt.ylabel('ADC Value')
plt.title('ADC Data - Channel 0 from Both Devices (TDD Synchronized)')
plt.legend()
plt.grid(True)
plt.savefig("Data channels 0 of both devices - Synchronized")
plt.close()  # Close the figure to free memory

print("Synchronized data capture complete!")

num_captures = 1000
phase_shifts_samples = []
phase_shifts_degrees = []
correlation_peaks = []

# Phase Shift Analysis using Cross-Correlation
print("\n--- Phase Shift Analysis ---")
print(f"Performing {num_captures} captures for cross-correlation analysis...")

sampling_rate = multi.dev1.sampling_rate
print(f"Sampling rate: {sampling_rate} Hz")

for i in range(num_captures):
    if (i + 1) % 10 == 0:
        print(f"Progress: {i + 1}/{num_captures} captures")

    # Capture synchronized data
    data1, data2 = multi.rx()

    # Normalize signals (remove DC offset and normalize amplitude)
    data1_norm = (data1 - np.mean(data1)) / np.std(data1)
    data2_norm = (data2 - np.mean(data2)) / np.std(data2)

    # Compute cross-correlation using FFT (much faster for large arrays)
    # This is equivalent to np.correlate(data1_norm, data2_norm, mode='full')
    # but uses FFT for O(N log N) complexity instead of O(N^2)
    fft1 = np.fft.fft(data1_norm, n=2*len(data1_norm))
    fft2 = np.fft.fft(data2_norm, n=2*len(data2_norm))
    correlation = np.fft.ifft(fft1 * np.conj(fft2)).real

    # Rearrange to match 'full' mode output (shift zero-lag to center)
    correlation = np.concatenate([correlation[len(data1):], correlation[:len(data1)]])

    # Find the lag with maximum correlation
    max_corr_idx = np.argmax(correlation)
    lag = max_corr_idx - (len(data1) - 1)  # Offset to center

    # Store results
    phase_shifts_samples.append(lag)
    correlation_peaks.append(correlation[max_corr_idx])

    # Calculate phase shift in degrees (if signal is periodic)
    # For a sinusoidal signal, we can estimate phase shift
    # Phase shift in samples / samples per period * 360 degrees
    # We'll store the sample shift for now and convert later if needed

# Convert to numpy arrays for analysis
phase_shifts_samples = np.array(phase_shifts_samples)
correlation_peaks = np.array(correlation_peaks)

# Statistical analysis
mean_shift = np.mean(phase_shifts_samples)
std_shift = np.std(phase_shifts_samples)
median_shift = np.median(phase_shifts_samples)

print(f"\nPhase Shift Statistics (in samples):")
print(f"  Mean: {mean_shift:.3f} samples")
print(f"  Std Dev: {std_shift:.3f} samples")
print(f"  Median: {median_shift:.3f} samples")
print(f"  Min: {np.min(phase_shifts_samples)} samples")
print(f"  Max: {np.max(phase_shifts_samples)} samples")

# Time delay in seconds
time_delay_mean = mean_shift / sampling_rate
time_delay_std = std_shift / sampling_rate
print(f"\nTime Delay:")
print(f"  Mean: {time_delay_mean*1e9:.3f} ns")
print(f"  Std Dev: {time_delay_std*1e9:.3f} ns")

# Create comprehensive analysis plots
fig = plt.figure(figsize=(16, 12))

# Plot 1: Histogram of phase shifts
ax1 = plt.subplot(3, 2, 1)
plt.hist(phase_shifts_samples, bins=50, edgecolor='black', alpha=0.7)
plt.axvline(mean_shift, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_shift:.2f}')
plt.axvline(median_shift, color='green', linestyle='--', linewidth=2, label=f'Median: {median_shift:.2f}')
plt.xlabel('Phase Shift (samples)')
plt.ylabel('Frequency')
plt.title('Distribution of Phase Shifts Across 1000 Captures')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 2: Time series of phase shift
ax2 = plt.subplot(3, 2, 2)
plt.plot(phase_shifts_samples, alpha=0.6, linewidth=0.5)
plt.axhline(mean_shift, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_shift:.2f}')
plt.fill_between(range(num_captures),
                  mean_shift - std_shift,
                  mean_shift + std_shift,
                  alpha=0.2, color='red', label=f'±1σ: {std_shift:.2f}')
plt.xlabel('Capture Number')
plt.ylabel('Phase Shift (samples)')
plt.title('Phase Shift Over Time')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 3: Correlation peak values
ax3 = plt.subplot(3, 2, 3)
plt.plot(correlation_peaks, alpha=0.6, linewidth=0.5)
plt.axhline(np.mean(correlation_peaks), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(correlation_peaks):.2f}')
plt.xlabel('Capture Number')
plt.ylabel('Correlation Peak Value')
plt.title('Cross-Correlation Peak Strength')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 4: Example cross-correlation function
ax4 = plt.subplot(3, 2, 4)
# Perform one final capture to show the correlation function
data1_ex, data2_ex = multi.rx()
data1_norm_ex = (data1_ex - np.mean(data1_ex)) / np.std(data1_ex)
data2_norm_ex = (data2_ex - np.mean(data2_ex)) / np.std(data2_ex)
# Use FFT-based cross-correlation for speed
fft1_ex = np.fft.fft(data1_norm_ex, n=2*len(data1_norm_ex))
fft2_ex = np.fft.fft(data2_norm_ex, n=2*len(data2_norm_ex))
correlation_ex = np.fft.ifft(fft1_ex * np.conj(fft2_ex)).real
correlation_ex = np.concatenate([correlation_ex[len(data1_ex):], correlation_ex[:len(data1_ex)]])
lags_ex = np.arange(-len(data1_ex) + 1, len(data1_ex))

# Plot only around the peak for clarity
max_idx = np.argmax(correlation_ex)
window = 1000  # Show ±1000 samples around peak
start_idx = max(0, max_idx - window)
end_idx = min(len(correlation_ex), max_idx + window)

plt.plot(lags_ex[start_idx:end_idx], correlation_ex[start_idx:end_idx], linewidth=1)
plt.axvline(lags_ex[max_idx], color='red', linestyle='--', linewidth=2, label=f'Peak at lag={lags_ex[max_idx]}')
plt.xlabel('Lag (samples)')
plt.ylabel('Cross-Correlation')
plt.title('Example Cross-Correlation Function')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 5: Example synchronized signals (zoomed in)
ax5 = plt.subplot(3, 2, 5)
zoom_samples = min(1000, len(data1_ex))  # Show first 1000 samples
plt.plot(data1_ex[:zoom_samples], label='Device 1', alpha=0.7, linewidth=1)
plt.plot(data2_ex[:zoom_samples], label='Device 2', alpha=0.7, linewidth=1)
plt.xlabel('Sample Index')
plt.ylabel('ADC Value')
plt.title('Example Synchronized Signals (Zoomed)')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 6: Phase shift distribution (box plot)
ax6 = plt.subplot(3, 2, 6)
plt.boxplot(phase_shifts_samples, vert=True)
plt.ylabel('Phase Shift (samples)')
plt.title('Phase Shift Distribution (Box Plot)')
plt.grid(True, alpha=0.3, axis='y')
plt.text(0.5, mean_shift, f'Mean: {mean_shift:.2f}\nStd: {std_shift:.2f}',
         transform=ax6.get_yaxis_transform(), ha='left', va='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig("Phase_Shift_Analysis_1000_Captures")
plt.close()

print("\nPhase shift analysis complete!")
print(f"Analysis plot saved as: Phase_Shift_Analysis_{num_captures}_Captures.png")

# Summary report
print("\n" + "="*60)
print("PHASE SHIFT ANALYSIS SUMMARY")
print("="*60)
print(f"Number of captures: {num_captures}")
print(f"Sampling rate: {sampling_rate} Hz")
print(f"\nPhase alignment:")
if abs(mean_shift) < 1.0:
    print(f"  ✓ Excellent alignment (mean shift: {mean_shift:.3f} samples)")
elif abs(mean_shift) < 5.0:
    print(f"  ✓ Good alignment (mean shift: {mean_shift:.3f} samples)")
else:
    print(f"  ⚠ Measurable shift detected (mean shift: {mean_shift:.3f} samples)")

print(f"\nConsistency:")
if std_shift < 0.5:
    print(f"  ✓ Very consistent (σ = {std_shift:.3f} samples)")
elif std_shift < 2.0:
    print(f"  ✓ Consistent (σ = {std_shift:.3f} samples)")
else:
    print(f"  ⚠ Variable phase shift (σ = {std_shift:.3f} samples)")

print(f"\nCorrelation quality:")
mean_corr = np.mean(correlation_peaks)
print(f"  Mean correlation peak: {mean_corr:.3f}")
if mean_corr > 0.9:
    print(f"  ✓ Excellent correlation")
elif mean_corr > 0.7:
    print(f"  ✓ Good correlation")
else:
    print(f"  ⚠ Moderate correlation")
print("="*60)

# Cleanup buffers
multi.rx_destroy_buffer()