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


print("--Connecting to device")
dev = adi.QuadMxFE(uri="ip:10.72.162.37")

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies_chip_a = [0]*4
dev.rx_channel_nco_frequencies_chip_b = [0]*4
dev.rx_channel_nco_frequencies_chip_c = [0]*4
dev.rx_channel_nco_frequencies_chip_d = [0]*4

dev.tx_channel_nco_frequencies_chip_a = [0]*4
dev.tx_channel_nco_frequencies_chip_b = [0]*4
dev.tx_channel_nco_frequencies_chip_c = [0]*4
dev.tx_channel_nco_frequencies_chip_d = [0]*4

print("--Test mode states")
print("rx_test_mode_chip_a", dev.rx_test_mode_chip_a)
print("rx_test_mode_chip_b", dev.rx_test_mode_chip_b)
print("rx_test_mode_chip_c", dev.rx_test_mode_chip_c)
print("rx_test_mode_chip_d", dev.rx_test_mode_chip_d)
print("External attenuation level:",dev.external_hardwaregain)

dev.rx_enabled_channels = [0, 1, 2, 3]
# dev.tx_enabled_channels = [0, 1]
dev.rx_buffer_size = 2**16

# Setup DDS
dev.dds_enabled = [1]*64
# Set all to zero first
dev.dds_frequencies = [0]*64
scale = 0.9
toneFreq_Hz = 10000
dev.dds_single_tone(toneFreq_Hz, scale)

# # Read registers
# reg = 0x01
# for offset in range(10):
#     print(sdr._rxadc0.reg_read(reg+offset))


# Collect data
fsr = int(dev.rx_sampling_frequency)
for r in range(10):
    # Collect data
    print("--Pulling buffers")
    x = dev.rx()
    # Measure phase
    print("Channel offset", measure_phase(x[0], x[1]),"(Degrees)")
    (p, s) = measure_phase_and_delay(x[0], x[1])
    print("Across Chips Sample delay: ",s)
    # print("Phase delay: ",p,"(Degrees)")
    print("------------------")

    plt.plot(np.real(x[0]), label='1')
    plt.plot(np.real(x[1]), label='2')
    plt.legend()
    print("FYI: Close figure to do next capture")
    plt.show()
