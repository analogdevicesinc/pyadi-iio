

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
from adi.sshfs import sshfs
import scipy.signal as signal
def initCW(tddn):
    # Startup TDDN
    tddn.enable = False
    # Configure top level engine
    frame_length_ms = 1
    tddn.frame_length_ms = frame_length_ms
    off_time = frame_length_ms - 0.1
    # Configure component channels
    
    tddn_channels = {
        "TX_OFFLOAD_SYNC": 0,
        "RX_OFFLOAD_SYNC": 1,
        "TDD_ENABLE": 2,
        "RX_MXFE_EN": 3,
        "TX_MXFE_EN": 4,
        "TX_STINGRAY_EN": 5
    }
    # Assign channel properties for CW
    for key, value in tddn_channels.items():
        if value == 0 or value == 1:
            tddn.channel[value].on_raw = 0
            tddn.channel[value].off_raw = 0
            tddn.channel[value].on_ms = 0
            tddn.channel[value].off_ms = 0
            tddn.channel[value].polarity = True
            tddn.channel[value].enable = True
        elif value == 2 or value == 5:
            tddn.channel[value].on_raw = 0
            tddn.channel[value].off_raw = 0
            tddn.channel[value].on_ms = 0
            tddn.channel[value].off_ms = 0
            tddn.channel[value].polarity = False
            tddn.channel[value].enable = True
        else:
            tddn.channel[value].on_raw = 0
            tddn.channel[value].off_raw = 10
            tddn.channel[value].polarity = True
            tddn.channel[value].enable = True
    tddn.enable = True # Fire up TDD engine
    tddn.sync_internal = True # software enable TDD mode

def measure_phase(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


trx_lo_both = 3.8e9
url = "ip:192.168.0.1"
# Create radio
conv = adi.adrv9009_zu11eg(url)
tddn = adi.tddn(url)
conv.trx_lo = int(trx_lo_both)
conv.trx_lo_chip_b = int(trx_lo_both)
# Configure properties
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.tx_enabled_channels = [0,1,2,3]

conv.tx_hardwaregain_chan0 = -10
conv.tx_hardwaregain_chan1 = -10
conv.tx_hardwaregain_chan0_chip_b = -10
conv.tx_hardwaregain_chan1_chip_b = -10
conv.gain_control_mode_chan0 = "slow_attack"
conv.gain_control_mode_chan1 = "slow_attack"
conv.gain_control_mode_chan0_chip_b = "slow_attack"
conv.gain_control_mode_chan1_chip_b = "slow_attack"
conv.rx_buffer_size = 2 ** 16
conv.tx_cyclic_buffer = True
conv.tx_ddr_offload = True

#conv.tx_destroy_buffer()
initCW(tddn)
ssh = sshfs("ip:analog.local", "root", "analog")
stdout, stderr = ssh._run(f"busybox devmem 0x9c450088 w 0x1")

# Read properties
print("TRX LO %s" % (conv.trx_lo))
print("TRX LO %s" % (conv.trx_lo_chip_b))


# Send data
#conv.dds_enabled = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#conv.dds_frequencies = [25000000, 0, 25000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#conv.dds_scales = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#conv.dds_phases = [0, 0, 90000, 0, 0, 0, 90000, 0, 0, 0, 0, 0, 0, 0, 0, 0]

fs = float(conv.rx_sample_rate)
N = int(conv.rx_buffer_size)
fc = 5e6
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 1 * (i + 1j * q)
conv.tx_destroy_buffer()
conv.tx([iq, iq, iq, iq])
# Collect data
fsr = int(conv.rx_sample_rate)
tddn.sync_soft = 0
tddn.sync_soft = 1 # toggle to start
for r in range(10):
    
    x = conv.rx()
    print(measure_phase(x[0], x[1]))
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
    print("Iteration %d" % r)
plt.show()
plt.pause(10)
#conv.tx_destroy_buffer()
#conv.rx_destroy_buffer()

