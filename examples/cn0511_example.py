# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import sys
import time

import adi
import numpy as np

# Set up CN0511. Replace URI with the actual uri of your CN0511 for remote access.
uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
rpi_sig_gen = adi.cn0511(uri=uri)

# Replace ambient temperature value with actual temperature for temperature
# calibration:
ambient_temp = 32.0  # set the ambient temperature

# Enable temperature measurements:
rpi_sig_gen.temperature_enable = True
print("Temperature read enabled: ", rpi_sig_gen.temperature_enable)

# Enable transmit:
rpi_sig_gen.tx_enable = True
print("Output enabled: ", rpi_sig_gen.tx_enable)

# Enable amplifier:
rpi_sig_gen.amp_enable = True
print("Amplifier enabled: ", rpi_sig_gen.amp_enable)

# Calibrate temperature:
rpi_sig_gen.temperature_cal = ambient_temp

# Read temperature:
temp = rpi_sig_gen.temperature
print("Chip Temperature: " + str(temp) + "°C")

# Set calibrated output [output_power_dbm, output_frequency_Hz]:
rpi_sig_gen.calibrated_output = [-20, 4000000000]
print(
    "Output power calibrated set to: " + str(rpi_sig_gen.calibrated_output[0]) + " dBm"
)
print("Output Frequency is set to: " + str(rpi_sig_gen.calibrated_output[1]) + " Hz")

print("Sleeping for 15 secs")
# sleep 15 sec
for i in range(15):
    print(".", end="", flush=True)
    time.sleep(1)
print(".")

# Disable reading temperature:
rpi_sig_gen.temperature_enable = False
print("Temperature read enabled: ", rpi_sig_gen.temperature_enable)

# Turn off amplifier and disable output:
print("Disabling the amplifier and output...")
rpi_sig_gen.amp_enable = False
print("Amplifier enabled: ", rpi_sig_gen.amp_enable)
rpi_sig_gen.tx_enable = False
print("Output enabled: ", rpi_sig_gen.tx_enable)

# Check if board was calibrated in production
print("Board was calibrated in production: ", rpi_sig_gen.board_calibrated)
