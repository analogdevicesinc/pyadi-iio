# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import matplotlib.pyplot as plt
from scipy import signal

import adi

dev = adi.ad9081("ip:analog.local")

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * 4
dev.tx_channel_nco_frequencies = [0] * 4

dev.rx_main_nco_frequencies = [1000000000] * 4
dev.tx_main_nco_frequencies = [1000000000] * 4

dev.rx_enabled_channels = [0]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = ["odd"] * 4

dev.rx_buffer_size = 2 ** 16
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sample_rate)

# Set single DDS tone for TX on one transmitter
dev.dds_single_tone(fs / 10, 0.5, channel=0)

# Collect data
for r in range(20):
    x = dev.rx()

    f, Pxx_den = signal.periodogram(x, fs, return_onesided=False)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e5])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
