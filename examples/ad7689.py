# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Set up AD7689
ad7689 = adi.ad7689(uri="ip:analog")
ad_channel = 0

ad7689.rx_enabled_channels = [ad_channel]
ad7689.rx_buffer_size = 100

raw = ad7689.channel[0].raw
data = ad7689.rx()

print(data)
