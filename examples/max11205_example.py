# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys

import adi
import numpy as np

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

max11205_dev = adi.max11205(uri=my_uri)

chn = 0
max11205_dev.rx_output_type = "SI"
max11205_dev.rx_enabled_channels = [chn]
max11205_dev.rx_buffer_size = 40

data = max11205_dev.rx()
print(data)
