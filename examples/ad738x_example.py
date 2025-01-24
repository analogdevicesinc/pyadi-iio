# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import sys

import numpy as np

import adi

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

ad738x_dev = adi.ad738x(uri=my_uri, device_name="ad7381")
ad738x_dev.rx_annotated = True
ad738x_dev.rx_output_type = "SI"
ad738x_dev.rx_enabled_channels = [1, 2]

data = ad738x_dev.rx()

print(data)
