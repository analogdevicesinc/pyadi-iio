# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Set up AD7124
adpd188 = adi.adpd188(uri="ip:10.48.65.156")
adpd188._ctrl.context.set_timeout(0)
adpd188.rx_buffer_size = 8
adpd188.sample_rate = 10

data = adpd188.rx()

print(data)
print(adpd188._rx_channel_names)
