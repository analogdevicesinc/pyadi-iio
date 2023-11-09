import sys
import time
from test.eeprom import read_fru_eeprom

import adi
import matplotlib.pyplot as plt
import numpy as np
import os

# Optionally pass URI as command line argument,
# else use default ip:analog.local

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# device connections

ad3552r = adi.ad3552r(uri=my_uri, device_name="ad3552r")

# device configurations

# Upstream ad3552r driver supports triggered buffer transfer so we will use that.
# We need to enable the buffer, set buffer lenght, and enable scan elements.
# Fill the buffer with output to DAC.
# Create sysfs trigger and attatch it to the buffer/device.
# Fire the trigger so the driver pushes buffer data to DAC device.

# Create sysfs trigger
trigger_index="0"
trigger_name="trigger0"
os.system("echo "+trigger_index+"> /sys/bus/iio/devices/iio_sysfs_trigger/add_trigger")

# Set default trigger
dac_trigger = self._ctx.find_device(trigger_name)
ad3552r._txdac._set_trigger(dac_trigger)

# Generate TX signal
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

ad3552r.tx_enabled_channels = [0, 1]
ad3552r.tx_cyclic_buffer = True
ad3552r.tx([samples, samples])

plt.suptitle("AD355R Samples data")
plt.plot(t, np.bitwise_xor(32768, samples))
plt.xlabel("Samples")
plt.show()

ad3552r.tx_destroy_buffer()
