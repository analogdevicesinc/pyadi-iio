# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Set up DAQ2
daq = adi.DAQ2(uri="ip:192.168.86.44")

# Transmit a tone with the DDS API
daq.dds_single_tone(200000000, 0.5)

# Collect data
fs = float(daq.sample_rate)
for r in range(40):
    x = daq.rx()
    f, Pxx_den = signal.periodogram(x[0], fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
