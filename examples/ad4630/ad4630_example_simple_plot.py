# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import adi
import matplotlib.pyplot as plt
import numpy as np

device_name = "ad4630-23"

adc = ad4630(uri="ip:192.168.0.130", device_name=device_name)
adc.rx_buffer_size = 500
adc.sample_rate = 2000000

try:
    adc.sample_averaging = 16
except:
    print("Sample average not supported in this mode")

data = adc.rx()

for ch in range(0, len(data)):
    x = np.arange(0, len(data[ch]))
    plt.figure(adc._ctrl._channels[ch]._name)
    plt.plot(x, data[ch])
plt.show()
