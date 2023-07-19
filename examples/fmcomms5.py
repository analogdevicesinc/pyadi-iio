# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Create radio
sdr = adi.FMComms5(uri="ip:analog")

# Configure properties
sdr.rx_lo = 2000000000
sdr.rx_lo_chip_b = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_lo_chip_b = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain_chan0 = -30
sdr.tx_hardwaregain_chip_b_chan0 = -30
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chip_b_chan0 = "slow_attack"
sdr.sample_rate = 1000000

# Set single DDS tone for TX on one transmitter
sdr.dds_single_tone(30000, 0.9)

# Read properties
fs = int(sdr.sample_rate)
print("RX LO %s" % (sdr.rx_lo))

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x[0], fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)

    f, Pxx_den = signal.periodogram(x[1], fs)
    plt.semilogy(f, Pxx_den)

    f, Pxx_den = signal.periodogram(x[2], fs)
    plt.semilogy(f, Pxx_den)

    f, Pxx_den = signal.periodogram(x[3], fs)
    plt.semilogy(f, Pxx_den)

    plt.ylim([1e-7, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
