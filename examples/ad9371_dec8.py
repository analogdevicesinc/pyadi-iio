# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Create radio
sdr = adi.ad9371(uri=my_uri)

# Configure properties
sdr.rx_enabled_channels = [0, 1]
sdr.tx_enabled_channels = [0, 1]
sdr.rx_lo = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain_chan0 = -30
sdr.tx_hardwaregain_chan1 = -30
sdr.gain_control_mode = "automatic"

# Enable int8 filter in FPGA
sdr.tx_enable_int8 = False
print("TX FS Pre int8:", sdr.tx_sample_rate)
sdr.tx_enable_int8 = True
print("TX FS Post int8:", sdr.tx_sample_rate)
fs = int(sdr.tx_sample_rate)

# Read properties
print("RX LO %s" % (sdr.rx_lo))

# Create a sinewave waveform
N = 2 ** 15
fc = 6000000
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

fc = -3000000
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq2 = i + 1j * q

# Send data
sdr.tx([iq, iq2])

# Collect data
fsr = int(sdr.rx_sample_rate)
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x[0], fsr)
    f2, Pxx_den2 = signal.periodogram(x[1], fsr)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.semilogy(f2, Pxx_den2)
    plt.ylim([1e-7, 1e4])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
