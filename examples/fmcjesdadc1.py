# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Create radio
rx = adi.fmcjesdadc1(uri="ip:analog")
tx = adi.Pluto()

# Configure tx properties
tx.tx_lo = 2000000000
tx.tx_cyclic_buffer = True
tx.tx_hardwaregain_chan0 = -30
tx.gain_control_mode_chan0 = "slow_attack"

# Create a sinewave waveform
fs = int(tx.sample_rate)
N = 1024
fc = int(3000000 / (fs / N)) * (fs / N)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

# Send data
tx.tx(iq)

# Collect data
for r in range(20):
    x = rx.rx()
    f, Pxx_den = signal.periodogram(x, fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
