# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import adi

# Set up AD7124
# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="AD7124 Example Script")
parser.add_argument(
    "-u",
    default=["ip:analog.local"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
args = parser.parse_args()
my_uri = args.u[0]

print("uri: " + str(my_uri))

ad7124 = adi.ad7124(uri=my_uri)
ad_channel0 = 0  # voltage0-voltage1 plug to CH1 on my m2k
ad_channel1 = 1  # voltage2-voltage3 plug to CH2 on my m2k

sc = ad7124.scale_available

ad7124.channel[ad_channel0].scale = sc[-1]  # get highest range
ad7124.channel[ad_channel1].scale = sc[-1]  # get highest range
ad7124.rx_output_type = "SI"
# sets sample rate for all channels
ad7124.sample_rate = 19200
ad7124.rx_enabled_channels = [ad_channel0, ad_channel1]
ad7124.rx_buffer_size = 100
ad7124._ctx.set_timeout(100000)

data = ad7124.rx()

print(data)

plt.figure(1)
plt.title(f"{ad7124._ctrl.name} @{ad7124.sample_rate}sps")
plt.ylabel("Volts")
plt.xlabel("Sample Number")
plt.plot(data[0], label=ad7124.channel[ad_channel0].name, color="orange", linewidth=2)
plt.plot(data[1], label=ad7124.channel[ad_channel1].name, color="blue", linewidth=2)
plt.show()

del ad7124
