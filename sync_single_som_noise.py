import time

import adi
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import scipy.io as sio

def measure_phase_and_delay(chan0, chan1, window=None):
    assert len(chan0) == len(chan1)
    if window==None:
        window = len(chan0)
    phases = []
    delays = []
    indx = 0
    sections = len(chan0)//window
    for sec in range(sections):
        chan0_tmp = chan0[indx:indx+window]
        chan1_tmp = chan1[indx:indx+window]
        indx = indx+window+1
        cor = np.correlate(chan0_tmp, chan1_tmp, "full")
        # plt.plot(np.real(cor))
        # plt.plot(np.imag(cor))
        # plt.plot(np.abs(cor))
        # plt.show()
        i = np.argmax(np.abs(cor))
        m = cor[i]
        sample_delay = len(chan0_tmp) - i - 1
        phases.append(np.angle(m)*180/np.pi)
        delays.append(sample_delay)
    return (np.mean(phases), np.mean(delays))

def measure_phase(chan0, chan1):
    assert len(chan0) == len(chan1)
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


buff_size= 2 ** 17

# Create radio
uri1 = "ip:192.168.86.36"

print("--Connecting to devices")
master = adi.adrv9009_zu11eg(uri1)

# Configure properties
print("--Setting up transceivers")
LO = 1000000000
master.rx_enabled_channels = [0, 1, 2, 3]
master.tx_enabled_channels = [0, 1]
master.trx_lo = LO
master.trx_lo_chip_b = LO
master.tx_hardwaregain_chan0 = -10
master.tx_hardwaregain_chan1 = -10
master.tx_hardwaregain_chan0_chip_b = -10
master.tx_hardwaregain_chan1_chip_b = -10
master.gain_control_mode = "manual"
master.gain_control_mode_chip_b = "manual"
master.rx_hardwaregain_chan0 = 25
master.rx_hardwaregain_chan1 = 25
master.rx_hardwaregain_chan0_chip_b = 25
master.rx_hardwaregain_chan1_chip_b = 25
master.rx_buffer_size = buff_size

# Generate noise
B = 2**15 * 0.8
s = np.random.uniform(-B,B,buff_size*4)
master.tx([s,s])
window = buff_size//16

# Read properties
print("TRX LO1 %s" % (master.trx_lo))
print("TRX LO2 %s" % (master.trx_lo_chip_b))

# Collect data
fsr = int(master.rx_sample_rate)
for r in range(10):
    # Collect data
    print("--Pulling buffers")
    x = master.rx()
    # Measure phase
    (p, s) = measure_phase_and_delay(x[0], x[1], window)
    print("###########")
    print("Same Chip Sample delay: ",s)
    print("Same Chip Phase delay: ",p,"(Degrees)")
    (p, s) = measure_phase_and_delay(x[0], x[2], window)
    print("Across Chips Sample delay: ",s)
    print("Across Chips Phase delay: ",p,"(Degrees)")
    print("------------------")


#     plt.plot(np.real(x[0]), label='1')
#     plt.plot(np.real(x[1]), label='2')
#     plt.plot(np.real(x[2]), label='3')
#     plt.legend()
#
# plt.show()
