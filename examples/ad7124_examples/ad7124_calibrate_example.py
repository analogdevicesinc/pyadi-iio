# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
from time import sleep

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

my_ad7124 = adi.ad7124(uri=my_uri)

print(
    "Welcome to the ad7124 calibration example script, where the local temperature is ",
    my_ad7124.temp(),
    " degrees C.",
)

input("Set input voltage close to zero, then press enter...")

print("Initial voltage on channel voltage0_voltage1: ", my_ad7124.voltage0_voltage1())

my_ad7124.voltage0_voltage1.sys_calibration_mode = "zero_scale"
my_ad7124.voltage0_voltage1.sys_calibration = 1
sleep(0.5)
print(
    "Calibrated zero-scale voltage on channel voltage0_voltage1: ",
    my_ad7124.voltage0_voltage1(),
)
print("Now set input voltage close to (but less than) 2.5 V")
input("Then press enter")

print(
    "Initial full-scale voltage on channel voltage0_voltage1: ",
    my_ad7124.voltage0_voltage1(),
)
my_ad7124.voltage0_voltage1.sys_calibration_mode = "full_scale"
my_ad7124.voltage0_voltage1.sys_calibration = 1
sleep(0.5)
print(
    "Calibrated full-scale voltage on channel voltage0_voltage1: ",
    my_ad7124.voltage0_voltage1(),
)


# del my_ad7124
