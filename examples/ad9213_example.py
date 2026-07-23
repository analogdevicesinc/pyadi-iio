# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = adi.ad9213(uri=my_uri)

my_adc.rx_buffer_size = 2048

print("Sampling frequency:", my_adc.sampling_frequency)

print("CHIP_ID_LSB  :", my_adc.ad9213_register_read(0x4))
print("CHIP_SCRATCH :", my_adc.ad9213_register_read(0xA))
print("Writing 0xAB to 0xA scratch register")
my_adc.ad9213_register_write(0xA, 0xAB)
print("CHIP_SCRATCH :", my_adc.ad9213_register_read(0xA))

# Collect RX data
data = my_adc.rx()

# Plot
x = np.arange(0, my_adc.rx_buffer_size)
fig, ax = plt.subplots(1, 1)
fig.suptitle("AD9213 Data")
ax.plot(x, data)
ax.set_ylabel("Amplitude")
ax.set_xlabel("Samples")
plt.show()

my_adc.rx_destroy_buffer()

del my_adc
