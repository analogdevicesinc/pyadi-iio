# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import adi

# Set up MAX9611
device = adi.max9611(uri="ip:analog.local")

for _ in range(3):
    print("Voltage Sense (input): ", device.voltage0.input)
    print("Voltage Input (raw): ", device.voltage1.raw)
    print("Voltage Input (offset): ", device.voltage1.offset)
    print("Voltage Input (scale): ", device.voltage1.scale)
    print("Current (input): ", device.current.input)
    print("Current (shunt resistor): ", device.current.shunt_resistor)
    print("Power (input): ", device.power.input)
    print("Power (shunt resistor): ", device.power.shunt_resistor)
    print("Temperature (raw): ", device.temp.raw)
    print("Temperature (scale): ", device.temp.scale)

    print("")
