# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np

url = "local:" if len(sys.argv) == 1 else sys.argv[1]
dev = adi.ad9094(url)

print("--Setting up chip")

dev.rx_enabled_channels = [0,1,2,3]
dev.rx_buffer_size = 2 ** 16

print(" CHIP_VENDOR_ID:", dev.register_read(0xC))

print("CHIP_SCRATCH phy is:", dev.register_read(0xA))
print("Writing 0xAB to 0xA scratch register")
dev.register_write(0xA,0xAB)
print("CHIP_SCRATCH phy is:", dev.register_read(0xA))

## test_mode_available value:
## off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp

dev.channel[0].test_mode = "ramp"
dev.channel[1].test_mode = "ramp"
dev.channel[2].test_mode = "off"
dev.channel[3].test_mode = "ramp"

x = dev.rx()

fig, axs = plt.subplots(4, 1)

axs[0].plot(x[0])
axs[0].set_title("Channel 0 data")
axs[0].set_xlabel("Sample")
axs[0].set_ylabel("Amplitude")

axs[1].plot(x[1])
axs[1].set_title("Channel 1 data")
axs[1].set_xlabel("Sample")
axs[1].set_ylabel("Amplitude")


axs[2].plot(x[2])
axs[2].set_title("Channel 2 data")
axs[2].set_xlabel("Sample")
axs[2].set_ylabel("Amplitude")

axs[3].plot(x[3])
axs[3].set_title("Channel 3 data")
axs[3].set_xlabel("Sample")
axs[3].set_ylabel("Amplitude")

plt.tight_layout()
plt.show()
