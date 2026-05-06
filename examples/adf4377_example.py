# Copyright (C) 2021-2025 Analog Devices, Inc.
# #
# # SPDX short identifier: ADIBSD


import adi

# Create pll instance connected to serial port
pll = adi.adf4377(uri="serial:/dev/ttyACM0,115200,8n1n")  # for Linux
# pll = adi.adf4377(uri="serial:/COM3,115200,8n1n") # for Windows

# configure PLL attributes
pll.reference_frequency = 100000000  # 100 MHz reference frequency
pll.reference_divider = 1  # Enable reference divider
pll.reference_doubler_enable = 0  # Disable reference doubler
pll.charge_pump_current = "11.100000"  # Set charge pump current to 11.1 mA


pll.volt0_frequency = 12000000000  # Set output frequency to 12 GHz
pll.volt0_en = 1  # Enable output channel 0
pll.volt0_output_power = 3  # Set output power to maximum level (640 mVpp)
pll.volt1_en = 0  # Disable output channel 1

# Configure SYSREF attributes
pll.sysref_delay_adjust = 50  # Set SYSREF delay adjustment to 50
pll.sysref_monitoring = 1  # Enable SYSREF monitoring
pll.sysref_invert_adjust = 0  # Set SYSREF invert adjustment to 0

# Raw register writes and reads using debug attribute
pll.reg_write("0x0A", "0x55")  # Use debug attribute to write to schratchpad
val = pll.reg_read(0x0A)  # Use debug attribute to read the schratchpad
print(hex(int(val)))
