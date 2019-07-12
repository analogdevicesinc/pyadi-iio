import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import time

# Create radio
sdr = adi.Pluto()

# Configure properties
sdr.rx_rf_bandwidth = 4000000
sdr.rx_lo = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain = -30
sdr.gain_control_mode = 'slow_attack'

# Read properties
print("RX LO %s" % (sdr.rx_lo))

# Create a sinewave waveform
fs = int(sdr.sample_rate)
fc = 3000000
N = 1024
ts = 1/float(fs)
t = np.arange(0, N*ts, ts)
i = np.cos(2*np.pi*t*fc) * 2**14
q = np.sin(2*np.pi*t*fc) * 2**14
iq = i + 1j*q

# Send data
sdr.tx(iq)

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x, fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e2])
    plt.xlabel('frequency [Hz]')
    plt.ylabel('PSD [V**2/Hz]')
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
