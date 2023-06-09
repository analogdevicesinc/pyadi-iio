# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
from scipy import signal

# Create radio
sdr = adi.adrv9009()

# Configure properties
sdr.rx_enabled_channels = [0, 1]
sdr.tx_enabled_channels = [0, 1]
sdr.trx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain_chan0 = -10
sdr.tx_hardwaregain_chan1 = -10
print(sdr.tx_hardwaregain_chan0)
print(sdr.tx_hardwaregain_chan1)
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"

# Read properties
print("TRX LO %s" % (sdr.trx_lo))

# Send data
sdr.dds_enabled = [1, 1, 1, 1, 1, 1, 1, 1]
sdr.dds_frequencies = [2000000, 0, 2000000, 0, 2000000, 0, 2000000, 0]
sdr.dds_scales = [1, 0, 1, 0, 1, 0, 1, 0]
sdr.dds_phases = [0, 0, 90000, 0, 0, 0, 90000, 0]


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
