# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad4130_dev = adi.ad4130("ip:analog")

chn = 0
ad4130_dev._rx_data_type = np.int32
ad4130_dev.rx_output_type = "SI"
ad4130_dev.rx_enabled_channels = [chn]
ad4130_dev.rx_buffer_size = 100

data = ad4130_dev.rx()

print(data)
