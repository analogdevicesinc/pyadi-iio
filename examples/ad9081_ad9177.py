import adi
import numpy as np
import scipy
from scipy import io
import os
from scipy import signal
import matplotlib.pyplot as plt

def gen_tone(fc, fs, N):
	fc = int(fc / (fs / N)) * (fs / N)
	ts = 1 / float(fs)
	t = np.arange(0, N * ts, ts)
	i = np.cos(2 * np.pi * t * fc) * 2 ** 14
	q = np.sin(2 * np.pi * t * fc) * 2 ** 14
	return i + 1j * q

dev = adi.ad9081("ip:10.48.65.139")
# dev.powerdown = 1
dev.powerdown = 0
dev.tx_sync_start = 'disarm'
dev.jesd204_fsm_ctrl = 1
# Set NCOs
dev.tx_channel_nco_frequencies = [0, 0, 0, 0]
dev.rx_channel_nco_frequencies = [0, 0, 0, 0]

dev.tx_dac_en = [1, 1, 1, 1]
dev.tx_channel_nco_phases = [0,0,0,0]

dev.tx_main_nco_frequencies = [2000000000, 2100000000, 2200000000, 2300000000]
dev.rx_main_nco_frequencies = [2000000000, 2100000000, 2200000000, 2300000000]
#dev.tx_main_nco_frequencies = [1000000000] * 4
#dev.rx_main_nco_frequencies = [1000000000] * 4

dev.tx_enabled_channels = [0, 1, 2, 3]
dev.rx_enabled_channels = [0, 1, 2, 3]

#dev.rx_nyquist_zone = ["odd"] * 4
dev.tx_cyclic_buffer = True
fs = int(dev.tx_sample_rate)
print("Sample Rate = ")
print(fs)
# Create arbitary sinewave waveform / buffer to pass to tx() method. Data buffers are actually read from custom HDL.
N = 2534
iq0_sine = gen_tone(10e6, fs, N)
dev.tx_ddr_offload = 1
dev.loopback_mode = 0
dev.tx_channel_nco_gain_scales = ([0.6, 0.6, 0.6, 0.6])
dev.tx([iq0_sine, iq0_sine, iq0_sine, iq0_sine])

dev.rx_buffer_size = 200

#for i in range(5):
data = dev.rx()
x = np.arange(0, dev.rx_buffer_size)
fig, (ch1, ch2, ch3, ch4) = plt.subplots(4, 1)
fig.suptitle("AD9081 Channels")
ch1.plot(x, data[0])
ch2.plot(x, data[1])
ch3.plot(x, data[2])
ch4.plot(x, data[3])
ch1.set_ylabel("Channel 1")
ch2.set_ylabel("Channel 2")
ch3.set_ylabel("Channel 3")
ch4.set_ylabel("Channel 4")
ch4.set_xlabel("Samples")

plt.show()
dev.rx_destroy_buffer()
dev.tx_destroy_buffer()
