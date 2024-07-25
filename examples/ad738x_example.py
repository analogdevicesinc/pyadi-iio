# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import adi
import numpy as np

ad738x_dev = adi.ad738x(uri="ip:analog", device_name="ad7381")
ad738x_dev.rx_annotated = True
ad738x_dev._rx_data_type = np.int32
ad738x_dev.rx_output_type = "SI"
ad738x_dev.rx_enabled_channels = [1, 2]

data = ad738x_dev.rx()

print(data)
