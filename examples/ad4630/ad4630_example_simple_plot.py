# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
parser = argparse.ArgumentParser(description="AD4630 Series Example Script")
parser.add_argument(
    "-u",
    "--uri",
    metavar="uri",
    default="ip:analog.local",
    help="An URI to the libiio context. e.g.: 'ip:analog.local'\
    'ip:192.168.1.3'\
    'serial:/dev/ttyUSB1,115200,8n1n'",
)
parser.add_argument(
    "-d",
    "--device",
    metavar="device",
    default="ad4630-24",
    help="Device name. e.g.: 'ad4030-24', 'ad4632-16', 'adaq4224'",
)

args = parser.parse_args()
print("uri: " + str(args.uri))
print("device: " + str(args.device))

if (
    args.device == "ad4030-24"
    or args.device == "ad4630-16"
    or args.device == "ad4630-24"
    or args.device == "ad4632-16"
    or args.device == "ad4632-24"
):
    adc = adi.ad4630(uri=args.ri, device_name=args.device)
elif (
    args.device == "adaq4224" or args.device == "adaq4216" or args.device == "adaq4220"
):
    adc = adi.adaq42xx(uri=args.uri, device_name=args.device)
else:
    print("Error: device: " + str(args.device) + " not supported.")
    quit()

adc.rx_buffer_size = 500
adc.sample_rate = 2000000

try:
    adc.sample_averaging = 16
except:
    print("Sample average not supported in this mode")

data = adc.rx()

for ch in range(0, len(data)):
    x = np.arange(0, len(data[ch]))
    plt.figure(adc._ctrl.channels[ch]._name)
    plt.plot(x, data[ch])
plt.show()
