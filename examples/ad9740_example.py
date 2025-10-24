import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument,
# else use default ip:analog.local

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# device connection
dev = adi.ad9740(uri=my_uri, device_name="ad9740")

dev.tx_enabled_channels = [0]
dev.tx_cyclic_buffer = True  # Cyclic mode for continuous playback

dev._tx_data_type = np.uint16

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

# Generate sine wave
# AD9740 is a 14-bit DAC (0-16383):
#   - Full scale (scale=1.0): sine amplitude = ±8191.5 around midpoint (8192)
#   - Half scale (scale=0.5): sine amplitude = ±4095.75 around midpoint (8192)
#   - Range: 0 to 16383
amplitude_scale = 1.0  # Full scale

# Sine generation (-1 to +1)
samples = np.sin(2 * np.pi * t * fc)
# Apply amplitude scaling for 14-bit DAC
samples *= amplitude_scale * 8191.5  # Full scale amplitude for 14-bit
# Offset to offset binary (mid-scale at 8192)
samples += 8192
# Clamp to valid 14-bit range and convert to uint16
samples = np.clip(samples, 0, 16383).astype(np.uint16)

print("sample rate:", dev.channel[0].sample_rate)
print(f"Amplitude scale: {amplitude_scale} (0.0 to 1.0)")
print(f"Signal frequency: {fc/1e3} kHz")
print("Sample data min:", samples.min())
print("Sample data max:", samples.max())
print("Number of samples:", len(samples))
print(f"AD9740: 14-bit DAC, midpoint at 8192, range: {samples.min()}-{samples.max()}")

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

plt.suptitle("AD9740 samples data")
plt.plot(t, samples)
plt.xlabel("Time (s)")
plt.ylabel("DAC Code (0-1023)")
plt.grid(True)

print("\n" + "="*60)
print("DAC is now outputting the waveform continuously!")
print("Close the matplotlib window to stop...")
print("="*60)

plt.show()  # Blocking call - keeps script running until window closed

print("\nStopping DAC and cleaning up...")
dev.tx_destroy_buffer()
print("Done!")
