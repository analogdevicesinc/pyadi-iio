import sys
import numpy as np

import adi 

# Optionally passs URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))


ad3552r_0 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-0")
ad3552r_1 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-1")


ad3552r_0.tx_enabled_channels = [0]
ad3552r_0.tx_enabled_channels = [1]
ad3552r_1.tx_enabled_channels = [0]
ad3552r_1.tx_enabled_channels = [1]

# Sample rate
fs = int(ad3552r_0.sample_rate)
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
samples = np.bitwise_xor(32768,samples)
ad3552r_0.tx_cyclic_buffer = True
ad3552r_1.tx_cyclic_buffer = True
ad3552r_0.tx(samples)
ad3552r_1.tx(samples)

input("Press Enter to stop the stream...")
