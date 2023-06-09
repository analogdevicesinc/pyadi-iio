# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Set up ADPD1080
adpd1080 = adi.adpd1080(uri="serial:COM23")
adpd1080.rx_buffer_size = 40
# adpd1080.sample_rate = 10

data = adpd1080.rx()

print(data)
print(adpd1080._rx_channel_names)
