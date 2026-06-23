# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

import adi

ad4170_dev = adi.ad4170("ip:analog")

chn = 0
ad4170_dev.rx_output_type = "SI"
ad4170_dev.rx_enabled_channels = [chn]
ad4170_dev.rx_buffer_size = 100

data = ad4170_dev.rx()

print(data)
