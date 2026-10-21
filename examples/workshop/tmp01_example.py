# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD-SWIOT1L-SL example: demonstrates channel attribute access on MAX14906,
temperature reading from ADT75, and buffered sampling from AD74413R.

Board configuration used in this example:
  - CH0: ad74413r, voltage_in   (analog voltage input, ADC)
  - CH1: ad74413r, voltage_in   (analog voltage input, ADC)
  - CH2: ad74413r, voltage_in   (analog voltage input, ADC)
  - CH3: ad74413r, voltage_in   (analog voltage input, ADC)

Adjust channel_device and channel_config below to match your wiring.
"""

import sys
import time

import matplotlib.pyplot as plt

import adi

# Optionally pass URI as command line argument
uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.97.41"
print(f"Connecting to AD-SWIOT1L-SL at {uri} ...")

# -- 1. Connect and configure the board --------------------------------------

board = adi.swiot1l(uri=uri)

# Switch to config mode to set channel functions
board.mode = "config"

# Re-connect after mode switch (firmware re-enumerates the IIO context)
board = adi.swiot1l(uri=uri)

board.ch0_device = "ad74413r"
board.ch0_function = "voltage_in"
board.ch0_enable = 1

board.ch1_device = "ad74413r"
board.ch1_function = "voltage_in"
board.ch1_enable = 1

board.ch2_device = "ad74413r"
board.ch2_function = "voltage_in"
board.ch2_enable = 1

board.ch3_device = "ad74413r"
board.ch3_function = "voltage_in"
board.ch3_enable = 1

# Switch to runtime mode — sub-devices become active
board.mode = "runtime"

# Re-connect once more after switching to runtime
board = adi.swiot1l(uri=uri)

# -- 2. ADT75: read temperature -----------------------------------------------

print("\n-- ADT75 temperature ------------------------------------------------")
temp_c = board.adt75()
print(f"  Temperature: {temp_c:.3f} °C")

# -- 3. AD74413R: continuous voltage read loop --------------------------------

print("\n-- AD74413R continuous read -----------------------------------------")
adc = board.ad74413r

print(f"  AD74413R rev ID: {adc.reg_read(0x46)}")
print(f"  AD74413R input (ADC) channels: {adc._rx_channel_names}")
print(f"  AD74413R output (DAC) channels: {adc._tx_channel_names}")

try:
    while True:
        ch = adc.channel["voltage3"]
        voltage_raw = ch.raw * ch.scale + ch.offset
        temperature_c = voltage_raw / 5 - 273.15

        print(f"  CH3: {voltage_raw:.1f} mV -> {temperature_c:.2f} °C")
        print("-" * 50)
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
