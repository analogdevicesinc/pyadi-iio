# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad4110_dev = adi.ad4110("ip:analog")

chn = 0
ad4110_dev.rx_output_type = "SI"
ad4110_dev.rx_enabled_channels = [chn]
ad4110_dev.rx_buffer_size = 100

data = ad4110_dev.rx()

print(data)
