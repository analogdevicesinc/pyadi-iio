# Copyright (C) 2022 Analog Devices, Inc.
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

device_name = "ad4630-24"

adc = adi.ad4630(uri=my_uri, device_name=device_name)
adc.rx_buffer_size = 500
adc.sample_rate = 2000000

try:
    adc.sample_averaging = 16
except:
    print("Sample average not supported in this mode")

data = adc.rx()

for ch in range(0, len(data)):
    x = np.arange(0, len(data[ch]))
    plt.figure(adc._ctrl.channels[ch]._name)
    plt.plot(x, data[ch])
plt.show()
