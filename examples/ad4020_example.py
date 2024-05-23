# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Optionally pass URI as command line argument,
# else use default context manager search
parser = argparse.ArgumentParser(description="AD4000 Series Example Script")
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
    default="ad4020",
    help="Device name. e.g.: 'ad4000', 'ad4020', 'adaq4003'",
)

args = parser.parse_args()
print("uri: " + str(args.uri))
print("device: " + str(args.device))

if args.device == "ad4000" or args.device == "ad4004" or args.device == "ad4008":
    my_adc = adi.ad4000(uri=args.uri, device_name=args.device)
elif args.device == "ad4001" or args.device == "ad4005":
    my_adc = adi.ad4001(uri=args.uri, device_name=args.device)
elif args.device == "ad4002" or args.device == "ad4006" or args.device == "ad4010":
    my_adc = adi.ad4002(uri=args.uri, device_name=args.device)
elif args.device == "ad4003" or args.device == "ad4007" or args.device == "ad4011":
    my_adc = adi.ad4003(uri=args.uri, device_name=args.device)
elif args.device == "ad4020" or args.device == "ad4021" or args.device == "ad4022":
    my_adc = adi.ad4020(uri=args.uri, device_name=args.device)
elif args.device == "adaq4001" or args.device == "adaq4003":
    my_adc = adi.adaq4003(uri=args.uri, device_name=args.device)
else:
    print("Error: device: " + str(args.device) + " not supported.")
    quit()

my_adc.rx_buffer_size = 4096

print("Sample Rate: ", my_adc.sampling_frequency)

data = my_adc.rx()

x = np.arange(0, len(data))
voltage = data * my_adc.voltage0.scale
dc = np.average(voltage)  # Extract DC component
ac = voltage - dc  # Extract AC component

plt.figure(1)
plt.clf()
plt.title(args.device.upper() + " Time Domain Data")
plt.plot(x, voltage)
plt.xlabel("Data Point")
plt.ylabel("Voltage (mV)")
plt.show()

f, Pxx_spec = signal.periodogram(
    ac, my_adc.sampling_frequency, window="flattop", scaling="spectrum"
)
Pxx_abs = np.sqrt(Pxx_spec)

plt.figure(2)
plt.clf()
plt.title(args.device.upper() + " Spectrum (Millivolts absolute)")
plt.semilogy(f, Pxx_abs)
plt.ylim([1e-6, 4])
plt.xlabel("frequency [Hz]")
plt.ylabel("Voltage (mV)")
plt.draw()
plt.show()

del my_adc
