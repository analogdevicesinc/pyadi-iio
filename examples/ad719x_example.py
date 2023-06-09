# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad719x_dev = adi.ad719x("ip:analog")

chn = 0
ad719x_dev._rx_data_type = np.int32
ad719x_dev.rx_output_type = "SI"
ad719x_dev.rx_enabled_channels = [chn]
ad719x_dev.rx_buffer_size = 100

data = ad719x_dev.rx()

print(data)
