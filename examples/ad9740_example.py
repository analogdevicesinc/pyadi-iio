import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import iio

import adi


def find_ad9740_device(uri):
    """
    Auto-detect AD9740 family device from the target system.
    Returns the device name if found, None otherwise.
    """
    try:
        ctx = iio.Context(uri)
        for dev in ctx.devices:
            if dev.name and 'ad97' in dev.name.lower():
                # Found an AD974x device
                return dev.name
    except Exception as e:
        print(f"Error scanning for devices: {e}")
    return None


# Optionally pass URI as command line argument,
# else use default ip:analog.local

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# Auto-detect the AD9740 family device
detected_device = find_ad9740_device(my_uri)

if detected_device:
    print(f"Auto-detected AD9740 family device: {detected_device}")
    dev = adi.ad9740(uri=my_uri, device_name=detected_device)
else:
    print("No AD9740 family device detected, trying default 'ad9740'...")
    # Try with default name - let the driver raise exception if it fails
    dev = adi.ad9740(uri=my_uri, device_name="ad9740")

dev.tx_enabled_channels = [0]
dev.tx_cyclic_buffer = True  # Cyclic mode for continuous playback

dev._tx_data_type = np.uint16

# Get the actual bit depth of the DAC
dac_bits = dev.output_bits[0] if dev.output_bits else 14
max_val = (1 << dac_bits) - 1  # 2^bits - 1
mid_val = 1 << (dac_bits - 1)  # 2^(bits-1) for midpoint
print(f"DAC resolution: {dac_bits} bits (range: 0-{max_val}, midpoint: {mid_val})")

# AD9740 sample rate (210 MHz from ADF4351)
# Note: The driver returns a default value since sampling_frequency
# attribute is not currently exposed by the kernel driver
fs = int(dev.channel[0].sample_rate)
print("Sample rate:", fs, "Hz")
# Signal frequency
fc = 100000  # 100 kHz sine wave (slower, easier to see)
# Number of samples - use multiple periods for smoother waveform
N = int(fs / fc) * 1  # 10 periods of the sine wave
# Period
ts = 1 / float(fs)
# Time array
t = np.arange(0, N * ts, ts)

# Generate sine wave adapted to DAC bit depth
# DAC bit depths:
#   - AD9748: 8-bit (0-255, midpoint 128)
#   - AD9740: 10-bit (0-1023, midpoint 512)
#   - AD9742: 12-bit (0-4095, midpoint 2048)
#   - AD9744: 14-bit (0-16383, midpoint 8192)
amplitude_scale = 1.0  # Full scale

# Sine generation (-1 to +1)
samples = np.sin(2 * np.pi * t * fc)
# Apply amplitude scaling for the actual DAC bit depth
samples *= amplitude_scale * (mid_val - 0.5)  # Full scale amplitude
# Offset to offset binary (mid-scale)
samples += mid_val
# Clamp to valid range and convert to uint16
samples = np.clip(samples, 0, max_val).astype(np.uint16)

print("sample rate:", dev.channel[0].sample_rate)
print(f"Amplitude scale: {amplitude_scale} (0.0 to 1.0)")
print(f"Signal frequency: {fc/1e3} kHz")
print("Sample data min:", samples.min())
print("Sample data max:", samples.max())
print("Number of samples:", len(samples))
print(f"{detected_device.upper() if detected_device else 'AD9740'}: {dac_bits}-bit DAC, midpoint at {mid_val}, range: {samples.min()}-{samples.max()}")

print(f"Cyclic buffer mode: {dev.tx_cyclic_buffer}")
print(f"Sending {len(samples)} samples to DAC...")

if dev.tx_cyclic_buffer == True:
    dev.tx(samples)
    print("Buffer sent in CYCLIC mode - should loop continuously")
    print("Keep this window open to keep the waveform playing")
else:
    for i in range(2):
        dev.tx(samples)
    print("Buffer sent in NON-CYCLIC mode - will play once")

plt.suptitle(f"{detected_device.upper() if detected_device else 'AD9740'} samples data ({dac_bits}-bit DAC)")
plt.plot(t, samples)
plt.xlabel("Time (s)")
plt.ylabel(f"DAC Code (0-{max_val})")
plt.grid(True)

print("\n" + "="*60)
print("DAC is now outputting the waveform continuously!")
print("Close the matplotlib window to stop...")
print("="*60)

plt.show()  # Blocking call - keeps script running until window closed

print("\nStopping DAC and cleaning up...")
dev.tx_destroy_buffer()
print("Done!")
