# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad777x_dev = adi.ad777x("ip:analog")

chn = 0
ad777x_dev.rx_output_type = "SI"
ad777x_dev.rx_enabled_channels = [chn]
ad777x_dev.rx_buffer_size = 100

data = ad777x_dev.rx()

print(data)
