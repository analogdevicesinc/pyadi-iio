# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))

# Create radio
sha3_reader = adi.sha_dev(uri=my_uri,device_name="sha3-reader")
ramp_reader = adi.sha_dev(uri=my_uri,device_name="ramp-reader")

# my_gpios = adi.one_bit_adc_dac(uri=my_uri)


sha3_reader.rx_buffer_size =2**12
ramp_reader.rx_buffer_size =2**12
sha3_reader.rx_enabled_channels=[0]
ramp_reader.rx_enabled_channels=[0]

my_gpios.gpio_ramp_reset = 1
my_gpios.gpio_sha_reset  = 1

data  = sha3_reader.rx()
data1 = ramp_reader.rx()

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(data)
plt.title('SHA3 Reader Data')

plt.subplot(2, 1, 2)
plt.plot(data1)
plt.title('Ramp Reader Data')

plt.show()

sha3_reader.rx_destroy_buffer()
ramp_reader.rx_destroy_buffer()
