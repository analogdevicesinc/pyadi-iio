# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

max = adi.max31855(uri=my_uri)
max.rx_buffer_size = 32

print(
    "Internal temperature: {} deg. C".format(
        str((max.temp_i.raw * max.temp_i.scale) / 1000)
    )
)
print(
    "Thermocouple temperature: {} deg. C".format(
        str((max.temp_t.raw * max.temp_t.scale) / 1000)
    )
)
