import time

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import adi

sdr = adi.adrv9002(uri="ip:192.168.86.58")
sdr.digital_gain_control_mode_chan0 = "Gain_Compensation_manual_control"
sdr.digital_gain_control_mode_chan1 = "Gain_Compensation_manual_control"
sdr.interface_gain_chan0 = "-12dB"
sdr.interface_gain_chan1 = "-12dB"
sdr.rx_ensm_mode_chan0 = "rf_enabled"
sdr.rx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_hardwaregain_chan0 = -20
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_cyclic_buffer = True

fs = int(sdr.rx0_sample_rate)

# Set single DDS tone for TX on one transmitter
sdr.dds_single_tone(-3000000, 0.9, channel=0)

# Create a sinewave waveform
# fc = 1000000
# N = 1024
# ts = 1 / float(fs)
# t = np.arange(0, N * ts, ts)
# i = np.cos(2 * np.pi * t * fc) * 2 ** 14
# q = np.sin(2 * np.pi * t * fc) * 2 ** 14
# iq = i + 1j * q
#
# # Send data
# sdr.tx(iq)

sdr.rx_buffer_size = 2 ** 18

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x, fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    # plt.ylim([1e-9, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)
