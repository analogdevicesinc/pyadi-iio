# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import sys
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import adi
from adi import ad7490

# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="AD7490 Example Script")
parser.add_argument(
    "-u",
    default=["serial:/dev/ttyACM0,57600,8n1"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:/dev/ttyACM0,57600,8n1n'",
    action="store",
    nargs="*",
)
args = parser.parse_args()
my_uri = args.u[0]

print("uri: " + str(my_uri))

# Set up AD7490
my_adc = adi.ad7490(uri=my_uri)
my_adc.rx_buffer_size = 200

# Choose Polarity
my_adc.polarity = "UNIPOLAR"
# my_adc.polarity = "BIPOLAR"

# Choose range:
my_adc.range = "REF_IN"
# my_adc.range = "2X_REF_IN"

# Choose output format:
my_adc.rx_output_type = "raw"
# my_adc.rx_output_type = "SI"

# Verify settings:
print("Polarity: ", my_adc.polarity)
print("Range: ", my_adc.range)
print("Sampling Frequency: ", my_adc.sampling_frequency)
print("Enabled Channels: ", my_adc.rx_enabled_channels)


plt.clf()
sleep(0.5)
data = my_adc.rx()
for ch in my_adc.rx_enabled_channels:
    plt.plot(range(0, len(data[0])), data[ch], label="voltage" + str(ch))
plt.xlabel("Data Point")
if my_adc.rx_output_type == "SI":
    plt.ylabel("Millivolts")
else:
    plt.ylabel("ADC counts")
plt.legend(
    bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
    loc="lower left",
    ncol=4,
    mode="expand",
    borderaxespad=0.0,
)
plt.pause(10)

del my_adc
