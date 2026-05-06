# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))


ada4355_dev = adi.ada4355(uri=my_uri)

ada4355_dev.rx_buffer_size = 8096
ada4355_dev.rx_enabled_channels = [0]
print("RX rx_enabled_channels: " + str(ada4355_dev.rx_enabled_channels))

print("Sampling Frequency: ", ada4355_dev.sampling_frequency)

# rx data

data = ada4355_dev.rx()

# plot setup

fig, (ch0) = plt.subplots(1, 1)

fig.suptitle("ADA4355 Data")
ch0.plot(data)
ch0.set_ylabel("Channel 0 amplitude")
ch0.set_xlabel("Samples")

plt.show()

ada4355_dev.rx_destroy_buffer()
