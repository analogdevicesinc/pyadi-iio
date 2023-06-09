# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Set up AD7606
ad7606 = adi.ad7606(uri="ip:analog")
ad_channel = 0

sc = ad7606.scale_available

ad7606.channel[ad_channel].scale = sc[-1]  # get highest range

ad7606.rx_enabled_channels = [ad_channel]
ad7606.rx_buffer_size = 100

raw = ad7606.channel[0].raw
data = ad7606.rx()

print(data)
