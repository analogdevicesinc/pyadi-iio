# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import adi
import matplotlib.pyplot as plt
import numpy as np
import time

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

# Synchronized multi-ADC capture using sharkbyte class
print("\n--- Synchronized Multi-ADC Capture (util_ext_sync) ---")
multi = adi.sharkbyte(
    uri=my_uri,
    device1_name="axi_adc1_hmcad15xx",
    device2_name="axi_adc2_hmcad15xx",
)

# Configure buffer size and enabled channels
multi.rx_buffer_size = 2**18
multi.rx_enabled_channels = [3]  # Apply to both devices

print("Multi-ADC rx_enabled_channels: " + str(multi.rx_enabled_channels))
print("RX SYNC START AVAILABLE:", multi.rx_sync_start_available)

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

# Perform 3 consecutive synchronized captures
num_captures = 3
captures_dev1 = []
captures_dev2 = []

print(f"\n--- Performing {num_captures} consecutive captures ---")
for i in range(num_captures):
    print(f"\n{'='*60}")
    print(f"Capture {i+1}/{num_captures}...")
    print(f"{'='*60}")
    # time.sleep(0.005)
    sync_data1, sync_data2 = multi.rx()
    captures_dev1.append(sync_data1)
    captures_dev2.append(sync_data2)

    # Quick alignment check - compare first 10 values
    print(f"\nQuick alignment check (first 10 samples):")
    print(f"  Dev1: {sync_data1[:10]}")
    print(f"  Dev2: {sync_data2[:10]}")

    # Calculate cross-correlation lag to check alignment
    # Normalize signals
    data1_norm = (sync_data1 - np.mean(sync_data1)) / np.std(sync_data1)
    data2_norm = (sync_data2 - np.mean(sync_data2)) / np.std(sync_data2)

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

# Create a figure with 3 rows (one for each capture)
fig, axes = plt.subplots(num_captures, 1, figsize=(14, 4*num_captures))

# Plot each capture
for i in range(num_captures):
    ax = axes[i] if num_captures > 1 else axes

    # Plot both devices for this capture
    ax.plot(captures_dev1[i], label="Device 1 - Channel 3", alpha=0.7, linewidth=1)
    ax.plot(captures_dev2[i], label="Device 2 - Channel 3", alpha=0.7, linewidth=1)

    ax.set_xlabel("Sample Index")
    ax.set_ylabel("ADC Value")
    ax.set_title(f"Capture {i+1} - Synchronized ADC Data (util_ext_sync)")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("3_consecutive_synchronized_captures.png")
print("\nPlot saved as: 3_consecutive_synchronized_captures.png")
plt.show()
plt.close()

print("\nSynchronized data capture complete!")

# Cleanup buffers
multi.rx_destroy_buffer()