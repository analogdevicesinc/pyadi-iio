import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import time

# Create radio
sdr = adi.ad9371()

# Configure properties
sdr.rx_enabled_channels = [0,1]
sdr.tx_enabled_channels = [0,1]
sdr.rx_lo = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain = -30
sdr.gain_control_mode = 'automatic'

# Enable digital loopback
# sdr.ctrl.debug_attrs['loopback_tx_rx'].value = '1'

# Read properties
print("RX LO %s" % (sdr.rx_lo))

# Create a sinewave waveform
N = 1024
fs = int(sdr.tx_sample_rate)
fc = 40000000
ts = 1/float(fs)
t = np.arange(0, N*ts, ts)
i = np.cos(2*np.pi*t*fc) * 2**14
q = np.sin(2*np.pi*t*fc) * 2**14
iq = i + 1j*q

fc = -30000000
i = np.cos(2*np.pi*t*fc) * 2**14
q = np.sin(2*np.pi*t*fc) * 2**14
iq2 = i + 1j*q

# Send data
sdr.tx([iq,iq2])

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
    plt.xlabel('frequency [Hz]')
    plt.ylabel('PSD [V**2/Hz]')
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
