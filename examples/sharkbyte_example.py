# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import adi
import matplotlib.pyplot as plt
import numpy as np

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))

# Initialize peripheral devices
gpio_controller = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")
ad5696_dev = adi.ad5686(uri=my_uri)

gpio_controller.gpio_clk_sel = 0

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

# Test pattern definitions
custom_pattern = 0x7FFF
fixed_test_pattern = 0x10
ramp_pattern = 0x40
pattern_disabled = 0x00

# Channel configuration - Set to 1, 2, or 4 channels
num_channels = 4  # Options: 1, 2, or 4

# Synchronized multi-ADC capture using sharkbyte class
print("\n--- Synchronized Multi-ADC Capture (util_ext_sync) ---")
print(f"Channel Mode: {num_channels} channel(s)")

multi = adi.sharkbyte(
    uri=my_uri,
    device1_name="axi_adc1_hmcad15xx",
    device2_name="axi_adc2_hmcad15xx",
    show_dma_arming=False # in order to see the DMA arming status, set it to True
)

# Configure buffer size and enabled channels based on num_channels
multi.rx_buffer_size = 2**14

if num_channels == 1:
    multi.rx_enabled_channels = [3]
    channel_list = [0]
elif num_channels == 2:
    multi.rx_enabled_channels = [0, 1]
    channel_list = [0, 1]
elif num_channels == 4:
    multi.rx_enabled_channels = [0, 1, 2, 3]
    channel_list = [0, 1, 2, 3]
else:
    raise ValueError(f"Invalid num_channels: {num_channels}. Must be 1, 2, or 4.")

print("Multi-ADC rx_enabled_channels: " + str(multi.rx_enabled_channels))
print("RX SYNC START AVAILABLE:", multi.rx_sync_start_available)

# Configure individual device settings via dev1 and dev2 properties
multi.dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev1.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev2.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev1.hmcad15xx_register_write(0x25, pattern_disabled)
multi.dev2.hmcad15xx_register_write(0x25, pattern_disabled)

# Set input selections for enabled channels only
# Input mapping for different channels
input_map_dev1 = ["IP4_IN4", "IP4_IN4", "IP4_IN4", "IP4_IN4"]  # Dev1: channels 0,1,2,3
input_map_dev2 = ["IP4_IN4", "IP4_IN4", "IP4_IN4", "IP4_IN4"]  # Dev2: channels 0,1,2,3

for ch in channel_list:
    multi.dev1.channel[ch].input_select = input_map_dev1[ch]
    multi.dev2.channel[ch].input_select = input_map_dev2[ch]
    print(f"Ch{ch}: Dev1={input_map_dev1[ch]}, Dev2={input_map_dev2[ch]}")

# Perform 3 consecutive synchronized captures
num_captures = 3
captures_dev1 = []
captures_dev2 = []

print(f"\n--- Performing {num_captures} consecutive captures ---")
for i in range(num_captures):
    print(f"\n{'='*60}")
    print(f"Capture {i+1}/{num_captures}...")
    print(f"{'='*60}")

    sync_data1, sync_data2 = multi.rx()
    captures_dev1.append(sync_data1)
    captures_dev2.append(sync_data2)

    # Quick alignment check on channel 0 - compare first 10 values
    # Handle both single channel (array) and multi-channel (list of arrays) cases
    if num_channels == 1:
        data1_ch0 = sync_data1
        data2_ch0 = sync_data2
    else:
        data1_ch0 = sync_data1[0]
        data2_ch0 = sync_data2[0]

    print(f"\nQuick alignment check - Channel 0 (first 10 samples):")
    print(f"  Dev1: {data1_ch0[:10]}")
    print(f"  Dev2: {data2_ch0[:10]}")

    # Calculate cross-correlation lag to check alignment on channel 0
    # Normalize signals
    data1_norm = (data1_ch0 - np.mean(data1_ch0)) / np.std(data1_ch0)
    data2_norm = (data2_ch0 - np.mean(data2_ch0)) / np.std(data2_ch0)

    # Use FFT-based cross-correlation for speed (only check first 10000 samples)
    check_len = min(10000, len(data1_norm))
    fft1 = np.fft.fft(data1_norm[:check_len], n=2*check_len)
    fft2 = np.fft.fft(data2_norm[:check_len], n=2*check_len)
    correlation = np.fft.ifft(fft1 * np.conj(fft2)).real
    correlation = np.concatenate([correlation[check_len:], correlation[:check_len]])

    # Find lag
    max_corr_idx = np.argmax(correlation)
    lag = max_corr_idx - (check_len - 1)

    print(f"  Alignment lag: {lag} samples")
    if abs(lag) < 5:
        print(f"  ✓ GOOD ALIGNMENT (lag < 5 samples)")
    else:
        print(f"  ✗ POOR ALIGNMENT (lag = {lag} samples)")

    print(f"\nCapture {i+1} complete!")

# Create plots for 3 consecutive captures
# Number of subplots depends on number of channels
num_plots_per_capture = num_channels
fig, axes = plt.subplots(num_captures, num_plots_per_capture,
                         figsize=(7*num_plots_per_capture, 4*num_captures))

# Reshape axes for easier indexing
if num_captures == 1 and num_plots_per_capture == 1:
    axes = np.array([[axes]])
elif num_captures == 1:
    axes = axes.reshape(1, -1)
elif num_plots_per_capture == 1:
    axes = axes.reshape(-1, 1)

# Plot each capture
for i in range(num_captures):
    for ch_idx, ch in enumerate(channel_list):
        ax = axes[i, ch_idx]

        # Extract data for this channel
        if num_channels == 1:
            data1 = captures_dev1[i]
            data2 = captures_dev2[i]
        else:
            data1 = captures_dev1[i][ch_idx]
            data2 = captures_dev2[i][ch_idx]

        # Plot both devices for this channel
        ax.plot(data1, label=f"Device 1 - Ch{ch}", alpha=0.7, linewidth=1)
        ax.plot(data2, label=f"Device 2 - Ch{ch}", alpha=0.7, linewidth=1)

        ax.set_xlabel("Sample Index")
        ax.set_ylabel("ADC Value")
        ax.set_title(f"Capture {i+1} - Channel {ch} Synchronized Data")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"3_consecutive_synchronized_captures_{num_channels}ch.png")
print(f"\nPlot saved as: 3_consecutive_synchronized_captures_{num_channels}ch.png")
plt.show()
plt.close()

# print("\n" + "="*70)
# print("PHASE SHIFT ANALYSIS - Multiple Captures")
# print("="*70)
# print(f"Channel Mode: {num_channels} channel(s)")
# print(f"Enabled Channels: {channel_list}")

# # Phase shift analysis configuration
# num_analysis_captures = 100  # Number of captures for phase shift analysis
# print(f"\nPerforming {num_analysis_captures} captures for phase shift analysis...")

# # Storage for analysis
# analysis_dev1 = []
# analysis_dev2 = []
# phase_shifts_samples = []
# correlation_peaks = []
# time_delays_ns = []

# sampling_rate = multi.dev1.sampling_rate
# print(f"Sampling rate: {sampling_rate} Hz")

# # Perform captures
# print(f"Note: Phase shift analysis will be performed on Channel 0 only")
# for i in range(num_analysis_captures):
#     if (i + 1) % 10 == 0:
#         print(f"Progress: {i + 1}/{num_analysis_captures} captures")

#     data1, data2 = multi.rx()
#     analysis_dev1.append(data1)
#     analysis_dev2.append(data2)

#     # Extract channel 0 for phase shift analysis
#     if num_channels == 1:
#         data1_ch0 = data1
#         data2_ch0 = data2
#     else:
#         data1_ch0 = data1[0]
#         data2_ch0 = data2[0]

#     # Normalize signals for cross-correlation
#     data1_norm = (data1_ch0 - np.mean(data1_ch0)) / np.std(data1_ch0)
#     data2_norm = (data2_ch0 - np.mean(data2_ch0)) / np.std(data2_ch0)

#     # FFT-based cross-correlation (faster for large arrays)
#     fft1 = np.fft.fft(data1_norm, n=2*len(data1_norm))
#     fft2 = np.fft.fft(data2_norm, n=2*len(data2_norm))
#     correlation = np.fft.ifft(fft1 * np.conj(fft2)).real

#     # Rearrange to match 'full' mode output
#     correlation = np.concatenate([correlation[len(data1_ch0):], correlation[:len(data1_ch0)]])

#     # Find lag with maximum correlation
#     max_corr_idx = np.argmax(correlation)
#     lag = max_corr_idx - (len(data1_ch0) - 1)

#     # Store results
#     phase_shifts_samples.append(lag)
#     correlation_peaks.append(correlation[max_corr_idx])
#     time_delays_ns.append((lag / sampling_rate) * 1e9)  # Convert to nanoseconds

# # Convert to numpy arrays for analysis
# phase_shifts_samples = np.array(phase_shifts_samples)
# correlation_peaks = np.array(correlation_peaks)
# time_delays_ns = np.array(time_delays_ns)

# # Calculate statistics
# mean_shift = np.mean(phase_shifts_samples)
# std_shift = np.std(phase_shifts_samples)
# median_shift = np.median(phase_shifts_samples)
# min_shift = np.min(phase_shifts_samples)
# max_shift = np.max(phase_shifts_samples)

# mean_time_delay = np.mean(time_delays_ns)
# std_time_delay = np.std(time_delays_ns)

# mean_corr = np.mean(correlation_peaks)
# min_corr = np.min(correlation_peaks)

# # Print statistical analysis
# print("\n" + "="*70)
# print("PHASE SHIFT STATISTICS")
# print("="*70)
# print(f"\nPhase Shift (in samples):")
# print(f"  Mean:     {mean_shift:.3f} samples")
# print(f"  Std Dev:  {std_shift:.3f} samples")
# print(f"  Median:   {median_shift:.3f} samples")
# print(f"  Min:      {min_shift} samples")
# print(f"  Max:      {max_shift} samples")
# print(f"  Range:    {max_shift - min_shift} samples")

# print(f"\nTime Delay:")
# print(f"  Mean:     {mean_time_delay:.3f} ns")
# print(f"  Std Dev:  {std_time_delay:.3f} ns")

# print(f"\nCorrelation Quality:")
# print(f"  Mean Peak:     {mean_corr:.4f}")
# print(f"  Min Peak:      {min_corr:.4f}")
# print(f"  Consistency:   {(1 - std_shift / (abs(mean_shift) + 1e-10)) * 100:.1f}%")

# # Alignment quality assessment
# print("\n" + "="*70)
# print("ALIGNMENT QUALITY ASSESSMENT")
# print("="*70)

# if abs(mean_shift) < 1.0:
#     print("  ✓✓✓ EXCELLENT alignment (mean shift < 1 sample)")
# elif abs(mean_shift) < 3.0:
#     print("  ✓✓ GOOD alignment (mean shift < 3 samples)")
# elif abs(mean_shift) < 10.0:
#     print("  ✓ ACCEPTABLE alignment (mean shift < 10 samples)")
# else:
#     print("  ✗ POOR alignment (mean shift >= 10 samples)")

# if std_shift < 0.5:
#     print("  ✓✓✓ VERY CONSISTENT (σ < 0.5 samples)")
# elif std_shift < 2.0:
#     print("  ✓✓ CONSISTENT (σ < 2 samples)")
# elif std_shift < 5.0:
#     print("  ✓ MODERATE consistency (σ < 5 samples)")
# else:
#     print("  ✗ POOR consistency (σ >= 5 samples)")

# if mean_corr > 0.95:
#     print("  ✓✓✓ EXCELLENT correlation (> 0.95)")
# elif mean_corr > 0.85:
#     print("  ✓✓ GOOD correlation (> 0.85)")
# elif mean_corr > 0.70:
#     print("  ✓ ACCEPTABLE correlation (> 0.70)")
# else:
#     print("  ✗ POOR correlation (<= 0.70)")

# print("="*70)

# # Create comprehensive analysis figure
# fig = plt.figure(figsize=(16, 12))

# # Plot 1: Median overlay - show signal consistency for Channel 0
# ax1 = plt.subplot(3, 3, 1)

# # Calculate median signal for both devices - channel 0
# if num_channels == 1:
#     # Single channel mode - data is already an array
#     analysis_dev1_ch0 = np.array(analysis_dev1)
#     analysis_dev2_ch0 = np.array(analysis_dev2)
# else:
#     # Multi-channel mode - extract channel 0
#     analysis_dev1_ch0 = np.array([capture[0] for capture in analysis_dev1])
#     analysis_dev2_ch0 = np.array([capture[0] for capture in analysis_dev2])

# median_dev1 = np.median(analysis_dev1_ch0, axis=0)
# median_dev2 = np.median(analysis_dev2_ch0, axis=0)

# # Show first 2000 samples for clarity
# zoom_len = min(2000, len(median_dev1))
# ax1.plot(median_dev1[:zoom_len], label='Device 1 Ch0 (Median)', linewidth=2, alpha=0.8)
# ax1.plot(median_dev2[:zoom_len], label='Device 2 Ch0 (Median)', linewidth=2, alpha=0.8)
# ax1.set_xlabel('Sample Index')
# ax1.set_ylabel('ADC Value')
# ax1.set_title(f'Ch0 Median Signal Overlay ({num_analysis_captures} captures)')
# ax1.legend()
# ax1.grid(True, alpha=0.3)

# # Plot 2: All captures overlay (semi-transparent to see density) - Channel 0
# ax2 = plt.subplot(3, 3, 2)
# for i in range(min(20, num_analysis_captures)):  # Show max 20 for visibility
#     ax2.plot(analysis_dev1_ch0[i][:zoom_len], color='blue', alpha=0.1, linewidth=0.5)
#     ax2.plot(analysis_dev2_ch0[i][:zoom_len], color='orange', alpha=0.1, linewidth=0.5)
# ax2.plot(median_dev1[:zoom_len], color='blue', label='Dev1 Ch0 Median', linewidth=2)
# ax2.plot(median_dev2[:zoom_len], color='orange', label='Dev2 Ch0 Median', linewidth=2)
# ax2.set_xlabel('Sample Index')
# ax2.set_ylabel('ADC Value')
# ax2.set_title(f'Ch0 Signal Overlay (first 20 of {num_analysis_captures})')
# ax2.legend()
# ax2.grid(True, alpha=0.3)

# # Plot 3: Phase shift histogram
# ax3 = plt.subplot(3, 3, 3)
# ax3.hist(phase_shifts_samples, bins=50, edgecolor='black', alpha=0.7)
# ax3.axvline(mean_shift, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_shift:.2f}')
# ax3.axvline(median_shift, color='green', linestyle='--', linewidth=2, label=f'Median: {median_shift:.2f}')
# ax3.set_xlabel('Phase Shift (samples)')
# ax3.set_ylabel('Frequency')
# ax3.set_title('Phase Shift Distribution')
# ax3.legend()
# ax3.grid(True, alpha=0.3)

# # Plot 4: Phase shift over time
# ax4 = plt.subplot(3, 3, 4)
# ax4.plot(phase_shifts_samples, alpha=0.6, linewidth=0.5, marker='.', markersize=2)
# ax4.axhline(mean_shift, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_shift:.2f}')
# ax4.fill_between(range(num_analysis_captures),
#                   mean_shift - std_shift,
#                   mean_shift + std_shift,
#                   alpha=0.2, color='red', label=f'±1σ: {std_shift:.2f}')
# ax4.set_xlabel('Capture Number')
# ax4.set_ylabel('Phase Shift (samples)')
# ax4.set_title('Phase Shift Over Time')
# ax4.legend()
# ax4.grid(True, alpha=0.3)

# # Plot 5: Time delay histogram (in nanoseconds)
# ax5 = plt.subplot(3, 3, 5)
# ax5.hist(time_delays_ns, bins=50, edgecolor='black', alpha=0.7, color='green')
# ax5.axvline(mean_time_delay, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_time_delay:.2f} ns')
# ax5.set_xlabel('Time Delay (ns)')
# ax5.set_ylabel('Frequency')
# ax5.set_title('Time Delay Distribution')
# ax5.legend()
# ax5.grid(True, alpha=0.3)

# # Plot 6: Correlation peak values over time
# ax6 = plt.subplot(3, 3, 6)
# ax6.plot(correlation_peaks, alpha=0.6, linewidth=0.5, marker='.', markersize=2, color='purple')
# ax6.axhline(mean_corr, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_corr:.4f}')
# ax6.set_xlabel('Capture Number')
# ax6.set_ylabel('Correlation Peak Value')
# ax6.set_title('Cross-Correlation Quality')
# ax6.legend()
# ax6.grid(True, alpha=0.3)

# # Plot 7: Phase shift box plot
# ax7 = plt.subplot(3, 3, 7)
# bp = ax7.boxplot([phase_shifts_samples], vert=True, patch_artist=True)
# bp['boxes'][0].set_facecolor('lightblue')
# ax7.set_ylabel('Phase Shift (samples)')
# ax7.set_title('Phase Shift Distribution (Box Plot)')
# ax7.grid(True, alpha=0.3, axis='y')
# ax7.set_xticklabels([f'{num_analysis_captures} captures'])

# # Plot 8: Example cross-correlation function
# ax8 = plt.subplot(3, 3, 8)
# # Use the median signals to show typical correlation
# median_dev1_norm = (median_dev1 - np.mean(median_dev1)) / np.std(median_dev1)
# median_dev2_norm = (median_dev2 - np.mean(median_dev2)) / np.std(median_dev2)
# fft1_ex = np.fft.fft(median_dev1_norm, n=2*len(median_dev1_norm))
# fft2_ex = np.fft.fft(median_dev2_norm, n=2*len(median_dev2_norm))
# correlation_ex = np.fft.ifft(fft1_ex * np.conj(fft2_ex)).real
# correlation_ex = np.concatenate([correlation_ex[len(median_dev1):], correlation_ex[:len(median_dev1)]])
# lags_ex = np.arange(-len(median_dev1) + 1, len(median_dev1))
# # Plot only around peak
# max_idx = np.argmax(correlation_ex)
# window = min(500, len(correlation_ex) // 4)
# start_idx = max(0, max_idx - window)
# end_idx = min(len(correlation_ex), max_idx + window)
# ax8.plot(lags_ex[start_idx:end_idx], correlation_ex[start_idx:end_idx], linewidth=1)
# ax8.axvline(lags_ex[max_idx], color='red', linestyle='--', linewidth=2, label=f'Peak at lag={lags_ex[max_idx]}')
# ax8.set_xlabel('Lag (samples)')
# ax8.set_ylabel('Cross-Correlation')
# ax8.set_title('Example Cross-Correlation (Median Signals)')
# ax8.legend()
# ax8.grid(True, alpha=0.3)

# # Plot 9: Summary statistics text
# ax9 = plt.subplot(3, 3, 9)
# ax9.axis('off')
# summary_text = f"""
# SUMMARY STATISTICS
# {'='*30}

# Analysis: Channel 0 only
# Mode: {num_channels} channel(s)

# Phase Shift:
#   Mean: {mean_shift:.3f} samples
#   Std:  {std_shift:.3f} samples
#   Range: [{min_shift}, {max_shift}]

# Time Delay:
#   Mean: {mean_time_delay:.3f} ns
#   Std:  {std_time_delay:.3f} ns

# Correlation:
#   Mean: {mean_corr:.4f}
#   Min:  {min_corr:.4f}

# Captures: {num_analysis_captures}
# Sampling Rate: {sampling_rate/1e6:.1f} MHz
# """
# ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
#          verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# plt.tight_layout()
# filename = f"Phase_Shift_Analysis_{num_analysis_captures}_Captures_{num_channels}ch.png"
# plt.savefig(filename, dpi=150)
# print(f"\nPhase shift analysis plot saved as: {filename}")
# plt.show()
# plt.close()

print("\nSynchronized data capture and analysis complete!")

# Cleanup buffers
multi.rx_destroy_buffer()