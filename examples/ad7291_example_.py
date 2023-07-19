# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Set up AD7291
my_ad7291 = adi.ad7291(uri=my_uri)

# Print out class retstring
print(my_ad7291)

# read out all channels, using each channel's call method
print("Temperature: ", my_ad7291.temp0(), " C")
print("Channel 0: ", my_ad7291.voltage0(), " millivolts")
print("Channel 1: ", my_ad7291.voltage1(), " millivolts")
print("Channel 2: ", my_ad7291.voltage2(), " millivolts")
print("Channel 3: ", my_ad7291.voltage3(), " millivolts")
print("Channel 4: ", my_ad7291.voltage4(), " millivolts")
print("Channel 5: ", my_ad7291.voltage5(), " millivolts")
print("Channel 6: ", my_ad7291.voltage6(), " millivolts")
print("Channel 7: ", my_ad7291.voltage7(), " millivolts")

del my_ad7291
