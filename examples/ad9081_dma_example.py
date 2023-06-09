# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def gen_tone(fc, fs, N):
    fc = int(fc / (fs / N)) * (fs / N)
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    return i + 1j * q


dev = adi.ad9081("ip:analog-2.local")

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

# Create a sinewave waveform
fs = int(dev.rx_sample_rate)
N = 1024
iq1 = gen_tone(-60e6, fs, N)
iq2 = gen_tone(100e6, fs, N)


# Enable BRAM offload in FPGA (Necessary for high rates)
dev.tx_ddr_offload = 1

# Send data
dev.tx(iq1)

# Collect data
for r in range(40):
    x = dev.rx()

    if r == 20:
        dev.tx_destroy_buffer()
        dev.tx(iq2)

    f, Pxx_den = signal.periodogram(x, fs, return_onesided=False)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-8, 1e5])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD")
    plt.draw()
    plt.pause(0.05)

plt.show()
