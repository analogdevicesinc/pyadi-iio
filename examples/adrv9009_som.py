# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def measure_phase(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


# Create radio
sdr = adi.adrv9009_zu11eg()

# Configure properties
sdr.rx_enabled_channels = [0, 1, 2, 3]
sdr.tx_enabled_channels = [0, 1]
sdr.trx_lo = 2000000000
sdr.trx_lo_chip_b = 2000000000
sdr.tx_hardwaregain_chan0 = -10
sdr.tx_hardwaregain_chan1 = -10
sdr.tx_hardwaregain_chan0_chip_b = -10
sdr.tx_hardwaregain_chan1_chip_b = -10
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"
sdr.gain_control_mode_chan0_chip_b = "slow_attack"
sdr.gain_control_mode_chan1_chip_b = "slow_attack"
sdr.rx_buffer_size = 2 ** 17

# Read properties
print("TRX LO %s" % (sdr.trx_lo))
print("TRX LO %s" % (sdr.trx_lo_chip_b))

# Send data
sdr.dds_enabled = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
sdr.dds_frequencies = [20000000, 0, 20000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
sdr.dds_scales = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
sdr.dds_phases = [0, 0, 90000, 0, 0, 0, 90000, 0, 0, 0, 0, 0, 0, 0, 0, 0]


# Collect data
fsr = int(sdr.rx_sample_rate)
for r in range(20):
    x = sdr.rx()
    print(measure_phase(x[0], x[1]))
    print(measure_phase(x[0], x[2]))
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
