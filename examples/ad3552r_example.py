import numpy as np

import adi

ad3552r = adi.ad3552r(uri="ip:analog-5.local")

ad3552r.tx_enabled_channels = [0]

# Sample rate
fs = int(ad3552r.sample_rate)
# Signal frequency
fc = 5000
# Number of samples
N = int(fs / fc)
# Period
ts = 1 / float(fs)
# Time array
t = np.arange(0, N * ts, ts)
# Sine generation
samples = np.sin(2 * np.pi * t * fc)
# Amplitude (full_scale / 2)
samples *= (2 ** 15) - 1
# Offset (full_scale / 2)
samples += 2 ** 15
# conversion to unsigned int
samples = np.uint16(samples)
# repetition of the array is needed
# as the SPI engine is ... limited
samples = np.repeat(samples, 2)

ad3552r.tx_cyclic_buffer = True
ad3552r.tx(samples)

input("Press Enter to stop the stream...")
