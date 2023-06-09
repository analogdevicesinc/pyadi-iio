# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Set up AD7124
adis16460 = adi.adis16460()

adis16460.rx_output_type = "SI"
adis16460.rx_enabled_channels = [4, 5]
adis16460.sample_rate = 2048
adis16460.rx_buffer_size = 100

data = adis16460.rx()

# print Y and Z axis acceleration
print(data)
