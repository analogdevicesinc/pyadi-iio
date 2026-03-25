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
resolution = 14 # Options: 8, 12, or 14 bits

my_uri = "ip:192.168.2.1" if len(sys.argv) == 1 else sys.argv[1]

print(f"Connecting to {my_uri}...")
print(f"Resolution: {resolution}-bit")

# Create two separate HMCAD15XX instances
adc1 = adi.hmcad15xx(uri=my_uri, device_name="axi_adc1_hmcad15xx")
adc2 = adi.hmcad15xx(uri=my_uri, device_name="axi_adc2_hmcad15xx")

adc1._rxadc.set_kernel_buffers_count(1)
adc2._rxadc.set_kernel_buffers_count(1)

# Configure based on resolution
if resolution in [8, 12]:
    # Single channel mode, all inputs to IN4
    mode = "SINGLE_CHANNEL"
    num_channels = 1

    # Set input to IN4 for all channels
    for ch in adc1.channel:
        ch.input_select = "IP4_IN4"
    for ch in adc2.channel:
        ch.input_select = "IP4_IN4"

    adc1.rx_enabled_channels = [0]
    adc2.rx_enabled_channels = [0]

    print(f"Mode: {mode}")
    print(f"All inputs set to IP4_IN4")

elif resolution == 14:
    # Quad channel mode, each channel gets its own input
    mode = "QUAD_CHANNEL"
    num_channels = 4
    # Set each channel to its corresponding input
    input_map = ["IP1_IN1", "IP2_IN2", "IP3_IN3", "IP4_IN4"]
    for i, ch in enumerate(adc1.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]
    for i, ch in enumerate(adc2.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]

    adc1.rx_enabled_channels = [0,1,2,3]
    adc2.rx_enabled_channels = [0,1,2,3]

    print(f"Mode: {mode}")
    print(f"Channel inputs: {input_map}")

else:
    raise ValueError(f"Invalid resolution: {resolution}. Use 8, 12, or 14.")

# Configure buffer size
N_rx = 2**18 
adc1.rx_buffer_size = N_rx
adc2.rx_buffer_size = N_rx

# Test pattern definitions
custom_pattern = 0x7FFF
fixed_test_pattern = 0x10
ramp_pattern = 0x40
pattern_disabled = 0x00

adc1.hmcad15xx_register_write(0x26, custom_pattern)
adc2.hmcad15xx_register_write(0x26, custom_pattern)
adc1.hmcad15xx_register_write(0x25, pattern_disabled)
adc2.hmcad15xx_register_write(0x25, pattern_disabled)

print(f"Buffer size: {N_rx} samples per channel")
print(f"Enabled channels: {num_channels}")

# Capture data
print("\nCapturing data...")
data1 = adc1.rx()
data2 = adc2.rx()

# Get sampling rate
fs = int(adc1.sampling_rate)
print(f"Sampling rate: {fs/1e6:.2f} MSPS")

# Select data for FFT analysis
if resolution == 14:
    fft_data1 = data1[3]
    fft_data2 = data2[3]
else:
    fft_data1 = data1
    fft_data2 = data2

# Compute FFT for ADC1
fft_result1 = np.fft.fft(fft_data1)
fft_freq1 = np.fft.fftfreq(len(fft_data1), 1/fs)

# Get magnitude and find peak (only positive frequencies) for ADC1
fft_mag1 = np.abs(fft_result1)
positive_freq_idx1 = fft_freq1 > 0
peak_idx1 = np.argmax(fft_mag1[positive_freq_idx1])
peak_freq1 = fft_freq1[positive_freq_idx1][peak_idx1]

# Compute FFT for ADC2
fft_result2 = np.fft.fft(fft_data2)
fft_freq2 = np.fft.fftfreq(len(fft_data2), 1/fs)

# Get magnitude and find peak (only positive frequencies) for ADC2
fft_mag2 = np.abs(fft_result2)
positive_freq_idx2 = fft_freq2 > 0
peak_idx2 = np.argmax(fft_mag2[positive_freq_idx2])
peak_freq2 = fft_freq2[positive_freq_idx2][peak_idx2]

print(f"ADC1 Peak frequency: {peak_freq1/1e6:.4f} MHz")
print(f"ADC2 Peak frequency: {peak_freq2/1e6:.4f} MHz")

# Plot data
if resolution == 14:
    plt.plot(data1[3][13000:13500], label="ADC1 Channel 0")
    plt.plot(data2[3][13000:13500], label="ADC2 Channel 0")
else:
    plt.plot(data1[13000:13500], label="ADC1 Channel 0")
    plt.plot(data2[13000:13500], label="ADC2 Channel 0")
plt.tight_layout()
plt.suptitle(f"Sharkbyte {resolution}-bit ADC Data", y=1.02)
plt.show()

# Cleanup
adc1.rx_destroy_buffer()
adc2.rx_destroy_buffer()
print("Done")
