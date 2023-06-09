# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
from time import sleep

import adi

VIN = "voltage0"
VIN_VDD = "voltage1"
TEMP_INT = "temp0"
TEMP_EXT = "temp1"
CIN1 = "capacitance0"
CIN1_DIFF = "capacitance0-capacitance2"
CIN2 = "capacitance1"
CIN2_DIFF = "capacitance1-capacitance3"

# Set up AD7746
dev = adi.ad7746(uri="serial:/dev/ttyACM0,115200,8n1", device_name="ad7746")
dev.channel[CIN1].offset = 66

input("[CALIB] 1. Remove the ruler and press ENTER. ")
m = dev.channel[CIN1].raw
input("[CALIB] 2. Place ruler to 51mm (2inch) and press ENTER.")
M = dev.channel[CIN1].raw

mm = (M - m) / 51

print(
    "[DEMO] Move the ruler around, its position will is read and displayed every 2 seconds.\n"
)

while True:
    capData = dev.channel[CIN1].raw
    capData -= m
    capData /= mm
    temperature = dev.channel[TEMP_INT].input
    temperature /= 1000.0
    print("Position: {} mm, Temperature: {} *C".format(int(capData), temperature))
    sleep(2)
