# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
from time import sleep

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Connect to CN0575
my_cn0575 = adi.cn0575(uri=my_uri)

print("\nReading onboard ADT75 ...")
print("Temperature: ", my_cn0575.adt75(), " deg. C")

print("Blinking LED and reading button:")
for i in range(1, 10):
    my_cn0575.led = 1
    sleep(0.5)
    my_cn0575.led = 0
    sleep(0.5)
    if my_cn0575.button == 1:
        print("Button Pressed")
    else:
        print("Button NOT Pressed")

# del my_cn0575
