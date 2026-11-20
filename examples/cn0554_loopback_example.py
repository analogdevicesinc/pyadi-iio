# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import sys
from time import sleep

import adi

# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="LM75 Example Script")
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

# Device initialization
try:
    my_adc = adi.ad7124(uri=my_uri)
    my_adc.rx_destroy_buffer()  # Just in case... this gives access to raw values.

except Exception as e:
    print(str(e))
    print("Failed to open AD7124 device")
    sys.exit(0)

try:
    my_dac = adi.ltc2688(uri=my_uri)

except Exception as e:
    print(str(e))
    print("Failed to open LTC2688 device")
    sys.exit(0)

print(
    "Welcome to the cn0554 loopback example script, where the local temperature is ",
    my_adc.temp(),
    " degrees C.",
)

# Set a staircase of voltages on DAC outputs. Single-ended or differential,
# Depending on how the AD7124 is configured.

staircase = "differential"

if staircase == "single_ended":
    print("Setting a single-ended staircase of voltages, 100 mV per channel...")
    my_dac.voltage0.volt = 100
    my_dac.voltage1.volt = 200
    my_dac.voltage2.volt = 300
    my_dac.voltage3.volt = 400
    my_dac.voltage4.volt = 500
    my_dac.voltage5.volt = 600
    my_dac.voltage6.volt = 700
    my_dac.voltage7.volt = 800
    my_dac.voltage8.volt = 900
    my_dac.voltage9.volt = 1000
    my_dac.voltage10.volt = 1100
    my_dac.voltage11.volt = 1200
    my_dac.voltage12.volt = 1300
    my_dac.voltage13.volt = 1400
    my_dac.voltage14.volt = 1500
    my_dac.voltage15.volt = 1600

if staircase == "differential":
    print("Setting a single-ended staircase of voltages, 100 mV per channel...")
    my_dac.voltage0.volt = 200
    my_dac.voltage1.volt = 100
    my_dac.voltage2.volt = 400
    my_dac.voltage3.volt = 100
    my_dac.voltage4.volt = 600
    my_dac.voltage5.volt = 100
    my_dac.voltage6.volt = 800
    my_dac.voltage7.volt = 100
    my_dac.voltage8.volt = 1000
    my_dac.voltage9.volt = 100
    my_dac.voltage10.volt = 1200
    my_dac.voltage11.volt = 100
    my_dac.voltage12.volt = 1400
    my_dac.voltage13.volt = 100
    my_dac.voltage14.volt = 1600
    my_dac.voltage15.volt = 100

sleep(0.5)

# AD7124 parameters
sampling_frequency = 19200
filter_type = "sinc3"

print("setting sample rate of all channels to ", sampling_frequency)
print("setting filter type of all channels to ", filter_type)
print("AD7124 channels:")

for i in range(0, len(my_adc.channel)):
    my_adc.channel[i].sampling_frequency = sampling_frequency
    my_adc.channel[i].filter_type = filter_type
    print("channel ", i, " name: ", my_adc.channel[i].name)

sleep(0.1)

print("Now reading out all raw channels...")

for i in range(0, len(my_adc.channel)):
    print("Channel ", i, ":  ", my_adc.channel[i].raw)

sleep(0.1)

my_adc.rx_destroy_buffer()  # Just in case... this gives access to raw values.

for i in range(0, len(my_adc.channel)):
    my_adc.channel[i].sampling_frequency = 4800

sleep(0.1)

# Clean up...
del my_dac
del my_adc
