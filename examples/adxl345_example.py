# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import time

import adi

# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="ADXL345 Example Script")
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

# Set up ADXL345
my_acc = adi.adxl345(uri=my_uri)
my_acc.rx_output_type = "SI"
my_acc.rx_buffer_size = 4
my_acc.rx_enabled_channels = [0, 1, 2]

sfa = my_acc.sampling_frequency_available
print("Sampling frequencies available:")
print(sfa)

print("\nX acceleration: " + str(my_acc.accel_x.raw))
print("Y acceleration: " + str(my_acc.accel_y.raw))
print("Z acceleration: " + str(my_acc.accel_z.raw))

print("\nSample rate: " + str(my_acc.sampling_frequency))

print("Setting sample rate to 12.5 sps...")
my_acc.sampling_frequency = 12.5
time.sleep(0.25)

print("new sample rate: " + str(my_acc.sampling_frequency))
my_acc.sampling_frequency = 100.0  # Set back to default
print("\nData using unbuffered rx(), SI (m/s^2):")
print(my_acc.rx())

my_acc.rx_output_type = "raw"
print("\nData using unbuffered rx(), raw:")
print(my_acc.rx())

del my_acc
