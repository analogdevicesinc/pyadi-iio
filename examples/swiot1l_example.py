# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD-SWIOT1L-SL example: demonstrates channel attribute access on MAX14906,
temperature reading from ADT75, and buffered sampling from AD74413R.

Board configuration used in this example:
  - CH0: ad74413r, voltage_in   (analog voltage input, ADC)
  - CH1: ad74413r, voltage_in   (analog voltage input, ADC)
  - CH2: ad74413r, current_in_ext (analog current input, ADC)
  - CH3: max14906, output        (digital output)

Adjust channel_device and channel_config below to match your wiring.
"""

import sys

import matplotlib.pyplot as plt

import adi

# Optionally pass URI as command line argument
uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.97.40"
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
board.ch2_function = "current_in_ext"
board.ch2_enable = 1

board.ch3_device = "max14906"
board.ch3_function = "output"
board.ch3_enable = 1

# Switch to runtime mode — sub-devices become active
board.mode = "runtime"

# Re-connect once more after switching to runtime
board = adi.swiot1l(uri=uri)

# 2. MAX14906: write and read back a digital output channel

print("\n-- MAX14906 digital output ------------------------------------------")
out_ch = board.max14906.channel["voltage3"]  # CH3 mapped to voltage3

out_ch.raw = 1
print(f"  voltage3 raw set to 1, readback: {out_ch.raw}")

out_ch.raw = 0
print(f"  voltage3 raw set to 0, readback: {out_ch.raw}")

# 3. ADT75: read temperature

print("\n-- ADT75 temperature ------------------------------------------------")
temp_c = board.adt75()
print(f"  Temperature: {temp_c:.3f} °C")

# 4. AD74413R: capture 1024 samples via IIO buffer

print("\n-- AD74413R buffered acquisition ------------------------------------")

adc = board.ad74413r
adc.rx_output_type = "SI"
adc.rx_enabled_channels = ["voltage0", "voltage1"]
adc.rx_buffer_size = 1024
adc.sample_rate = 4800

data = adc.rx()
adc.rx_destroy_buffer()

print(f"  Captured {len(data[0])} samples on each of {len(data)} channels")

# 5. Plot

fig, axes = plt.subplots(len(data), 1, sharex=True, figsize=(10, 4 * len(data)))
if len(data) == 1:
    axes = [axes]

channel_labels = ["CH0 - voltage_in (mV)", "CH1 - voltage_in (mV)"]

for ax, samples, label in zip(axes, data, channel_labels):
    ax.plot(samples)
    ax.set_ylabel(label)
    ax.grid(True)

axes[-1].set_xlabel("Sample")
fig.suptitle(f"AD-SWIOT1L-SL - AD74413R capture  |  ADT75: {temp_c:.2f} °C")
plt.tight_layout()
plt.show()
