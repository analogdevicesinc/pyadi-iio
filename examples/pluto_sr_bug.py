# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np

# Create radio
sdr = adi.Pluto(uri="ip:pluto.local")

# Configure properties
sdr.rx_rf_bandwidth = 4000000
sdr.rx_lo = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain_chan0 = -53
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 50

# Configuration data channels
sdr.rx_enabled_channels = [0]
sdr.tx_enabled_channels = [0]

# Read properties
print("RX LO %s" % (sdr.rx_lo))

# Create a sinewave waveform
fs = int(sdr.sample_rate)
N = 1024
fc = int(1000000 / (fs / N)) * (fs / N)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

# Send data
sdr.tx(iq)

# Collect data
for r in range(20):
    sdr.sample_rate = 7.5e6  # THIS SEEMS TO TOGGLE THE BEHAVIOR
    sdr.tx_destroy_buffer()
    sdr.tx(iq)

    # Wait for transmitter to become ready
    time.sleep(1)

    # Flush buffers
    for _ in range(100):
        x = sdr.rx()

    plt.clf()
    plt.plot(np.real(x))
    plt.plot(np.imag(x))
    plt.draw()

    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
