# Copyright (C) 2023-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Create pll instance connected to serial port
pll = adi.adf4382(uri="serial:/dev/ttyACM0,115200,8n1n")

# Configure pll attributes
pll.sw_sync_en = 0  # Disable sync
pll.reference_frequency = 125000000  # Input reference clock
pll.reference_doubler_en = 1  # Enable reference doubler
pll.reference_divider = 1  # Set reference divider
pll.charge_pump_current = "11.100000"  # Set charge pump current in mA

pll.altvolt0_frequency = 20000000000  # Output reference clock
pll.altvolt0_en = 1  # Enable output channel 0
pll.altvolt0_output_power = 9  # Set output amplitude of ch. 0
pll.altvolt1_en = 0  # Disable output channel 0

# Configure fast calibration
# pll.fastcal_en = 1  # Enable fast calibration
# pll.fastcal_lut_en = 1  # Enable use of fast calibration Look-Up Table

pll.reg_write("0x0A", "0x55")  # Use debug attribute to write to schratchpad
val = pll.reg_read(0x0A)  # Use debug attribute to read the schratchpad
print(hex(int(val)))
