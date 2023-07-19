# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

rtd = adi.max31865(uri=my_uri)
rtd.rx_buffer_size = 16

print("Fault Flag {} ".format(str(rtd.fault)))

print("Sampling Frequency Available {} Hz".format(str(rtd.samp_available)))

print("Notch Filter: {} Hz".format(str(rtd.filter.notch)))

datapoints = 5
for i in range(datapoints):

    print("RTD raw: {} ".format(str((rtd.temp.raw))))
    print("RTD scale: {} ".format(str((rtd.temp.scale))))
    time.sleep(0.1)
