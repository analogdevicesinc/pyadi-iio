# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Set up AD7124
ad7124 = adi.ad7124(uri="ip:10.48.65.138")
ad_channel = 0

sc = ad7124.scale_available

ad7124.channel[ad_channel].scale = sc[-1]  # get highest range
ad7124.rx_output_type = "SI"
# sets sample rate for all channels
ad7124.sample_rate = 19200
ad7124.rx_enabled_channels = [ad_channel]
ad7124.rx_buffer_size = 100

raw = ad7124.channel[0].raw
data = ad7124.rx()

print(data)
