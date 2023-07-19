# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys

import adi
import numpy as np

# Optionally pass URI as command line argument,
# else use default context manager search
# my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
my_uri = "ip:169.254.5.45"
print("uri: " + str(my_uri))

max14001_dev = adi.max14001(uri=my_uri)

chn = 0
raw = max14001_dev.channel[chn].raw
scale = max14001_dev.channel[chn].scale
offset = max14001_dev.channel[chn].offset
voltage = raw * scale + offset

print("raw: ", raw)
print("scale: ", scale)
print("offset: ", offset)
print("voltage: ", voltage)
