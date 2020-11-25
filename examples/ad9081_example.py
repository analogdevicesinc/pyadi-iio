import adi
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

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

def sub_phases(x, y):
    return ([e1-e2 for (e1, e2) in zip(x, y)])

def measure_and_adjust_phase_offset(chan0, chan1, phase_correction):
    assert len(chan0) == len(chan1)
    (p, s) = measure_phase_and_delay(chan0, chan1)
    #print("Across Chips Sample delay: ",s)
    #print("Phase delay: ",p,"(Degrees)")
    #print(phase_correction)
    return (sub_phases(phase_correction, [int(p*1000)]*4), s)

dev = adi.ad9081("ip:analog.local")

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies = [0]*4
dev.tx_channel_nco_frequencies = [0]*4

dev.rx_main_nco_frequencies = [1000000000]*4
dev.tx_main_nco_frequencies = [1000000000]*4

dev.rx_enabled_channels = [0]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = 'odd'

dev.rx_buffer_size = 2**16
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sampling_frequency)

# Set single DDS tone for TX on one transmitter
dev.dds_single_tone(fs / 10, 0.5, channel=0)

# Collect data
for r in range(20):
    x = dev.rx()
    f, Pxx_den = signal.periodogram(x, fs, return_onesided=False)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e5])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
