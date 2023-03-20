import sys
import time
from test.eeprom import read_fru_eeprom

import adi
import matplotlib.pyplot as plt
import numpy as np

# Optionally passs URI as command line argument,
# else use default ip:analog.local

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# device connections

ad3552r = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r")

# device configurations

ad3552r.tx_enabled_channels = [0, 1]
ad3552r.tx_cyclic_buffer = True

# signal generation
fs = int(ad3552r.sample_rate)
# Signal frequency
fc = 80000
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
# conversion to unsigned int and offset binary
samples = np.uint16(samples)
samples = np.bitwise_xor(32768, samples)



print("sample rate:", ad3552r.sample_rate)
print("Sample data min:", samples.min())
print("Sample data max:", samples.max())

# available options: "0/2.5V", "0/5V", "0/10V", "-5/+5V", "-10/+10V"

ad3552r.output_range = "-10/+10V"
print("output_range:dac:", ad3552r.output_range)

# available options:"adc_input", "dma_input", "ramp_input"

ad3552r.input_source = "dma_input"

print("input_source:dac:", ad3552r.input_source)
ad3552r.tx([samples, samples])

# available options:"start_stream_synced", "start_stream", "stop_stream"

ad3552r.stream_status = "start_stream"

plt.suptitle("AD355R Sanples data")
plt.plot(t, np.bitwise_xor(32768, samples))
plt.xlabel("Samples")
plt.show()

ad3552r.stream_status = "stop_stream"
ad3552r.tx_destroy_buffer()
