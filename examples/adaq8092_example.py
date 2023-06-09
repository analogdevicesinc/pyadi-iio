# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import matplotlib.pyplot as plt
import numpy as np
from adi import adaq8092

# Optionally pass URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = adaq8092(uri=my_uri)
my_adc.rx_buffer_size = 256
my_adc.rx_output_type = "raw"

print("Sampling frequency:", my_adc.sampling_frequency)
print("Enabled Channels: ", my_adc.rx_enabled_channels)

plt.clf()
data = my_adc.rx()
for ch in my_adc.rx_enabled_channels:
    plt.plot(range(0, len(data[0])), data[ch], label="channel" + str(ch))
plt.xlabel("Data Point")
plt.ylabel("ADC counts")
plt.legend(
    bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
    loc="lower left",
    ncol=4,
    mode="expand",
    borderaxespad=0.0,
)
plt.show()

del my_adc
