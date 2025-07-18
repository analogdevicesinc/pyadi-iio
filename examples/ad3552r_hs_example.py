import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument,
# else use default ip:analog.local

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
my_device = sys.argv[2] if len(sys.argv) >= 2 else "ad3552r"
print("uri: " + str(my_uri))

# device connection
dev = adi.ad3552r_hs(uri=my_uri, device_name=my_device)

print("INTERFACE_CONFIG_A:", dev.reg_read(0x00))
print("SCRATCH_PAD:", dev.reg_read(0x0A))
print("SCRATCH_PAD write: 1")
dev.reg_write(0x0A, 1)
print("SCRATCH_PAD:", dev.reg_read(0x0A))
print("SCRATCH_PAD write: 0")
dev.reg_write(0x0A, 0)
print("SCRATCH_PAD:", dev.reg_read(0x0A))

dev.tx_enabled_channels = [0, 1]
dev.tx_cyclic_buffer = True

dev._tx_data_type = np.uint16

# ad3552r is dual channel, the effective sample rate is:
# 1 / (1 / 33333333 + 1 / 33333333)) = 16666666
# if both channels are enabled in a buffered write.
fs = int(dev.channel[0].sample_rate) / 2
# Signal frequency
fc = 80000
# Number of samples
N = int(fs / fc)
# Period
ts = 1 / float(fs)
# Time array
t = np.arange(0, N * ts, ts)
# Sine generation
samples = np.sin(2 * np.pi * t * fc)
# Amplitude (full_scale / 2)
samples *= (2 ** 15) - 1
# Offset (full_scale / 2)
samples += 2 ** 15
# conversion to unsigned int and offset binary
samples = np.uint16(samples)

print("sample rate:", dev.channel[0].sample_rate)
print("Sample data min:", samples.min())
print("Sample data max:", samples.max())

if dev.tx_cyclic_buffer == True:
    dev.tx([samples, samples])
else:
    for i in range(2):
        dev.tx([samples, samples])

plt.suptitle("AD3552R samples data")
plt.plot(t, samples)
plt.xlabel("Samples")
plt.show()

dev.tx_destroy_buffer()
