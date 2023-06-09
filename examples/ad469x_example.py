# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad4696_dev = adi.ad469x(uri="ip:analog")

ad_channel = 0
ad4696_dev.rx_output_type = "SI"
ad4696_dev.rx_enabled_channels = [ad_channel]
ad4696_dev.rx_buffer_size = 100

data = ad4696_dev.rx()

print(data)
