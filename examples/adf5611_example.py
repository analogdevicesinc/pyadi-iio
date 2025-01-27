# Copyright (C) 2023-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Create a new AD5611 device Serial port connection instance
pll = adi.adf5611(
    uri="serial:/dev/ttyACM0,230400,8n1n"
)  # Change URI to your specific serial port

# Configure pll attributes
pll.reference_frequency = 122880000  # Set reference frequency to 122.88 MHz
pll.rfout_frequency = 12000000000  # Set RF output frequency to 12 GHz
pll.altvolt0_rfout_power = 3  # Set RF output power to 3 dBm
pll.reference_divider = 2  # Set reference divider to 1
pll.charge_pump_current = "3.200000"  # Set charge pump current to 3.2 mA

# Configure RfoutDiv Divider Output
pll.rfoutdiv_power = 0  # Set RfoutDiv Power to 0 dBm
pll.rfoutdiv_divider = "1"  # Set RfoutDiv Divider to 1
pll.en_rfoutdiv = 1  # Enable RfoutDiv Divider

pll.reg_write(0x0A, 0x5A)  # Write to register 0x0A with value 0x5A
val = pll.reg_read(0x0A)  # Read register 0x0A
print(hex(int(val)))  # Print the value of register 0x0A
