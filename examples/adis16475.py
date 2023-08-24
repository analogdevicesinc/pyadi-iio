# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Set up AD7124
adis16475 = adi.adis16475()

adis16475.rx_output_type = "raw"
adis16475.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6]
adis16475.sample_rate = 2000
adis16475.rx_buffer_size = 100

data = adis16475.rx()

# print Y and Z axis acceleration
print(data)
