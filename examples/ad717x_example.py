# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import numpy as np

ad717x_dev = adi.ad717x("ip:analog")

chn = 0
ad717x_dev._rx_data_type = np.int32
ad717x_dev.rx_output_type = "SI"
ad717x_dev.rx_enabled_channels = [chn]
ad717x_dev.rx_buffer_size = 100

data = ad717x_dev.rx()

print(data)
