# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

device_name = "adaq4224"

adc = adi.adaq42xx(uri=my_uri, device_name=device_name)
adc.rx_buffer_size = 500
adc.sample_rate = 2000000
try:
    adc.sample_averaging = 16
except:
    print("Sample average not supported in this mode")

# Available gains are 0.33, 0.56, 2.22, 6.67
# but due to Linux ABI technicalities they must be expressed with different values.

gains_avail = adc.chan0.scale_available

adc.chan0.scale = gains_avail[0]
print("Sampling with gain set to 0.33")

data = adc.rx()

for ch in range(0, len(data)):
    x = np.arange(0, len(data[ch]))
    plt.figure(adc._ctrl.channels[ch]._name)
    plt.plot(x, data[ch])
plt.title("Samples read with 0.33 gain")
plt.show()

adc.chan0.scale = gains_avail[1]
print("Sampling with gain set to 0.56")

data = adc.rx()

for ch in range(0, len(data)):
    x = np.arange(0, len(data[ch]))
    plt.figure(adc._ctrl.channels[ch]._name)
    plt.plot(x, data[ch])
plt.title("Samples read with 0.56 gain")
plt.show()
