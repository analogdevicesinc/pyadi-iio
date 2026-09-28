# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
from time import sleep

import matplotlib.pyplot as plt

import adi


def display_settings(sampling_frequency, rx_enabled_channels, common_mode_voltage):
    # def display_settings(sampling_frequency, rx_enabled_channels):
    print("Sampling Frequency: ", sampling_frequency)
    print("Enabled Channels: ", rx_enabled_channels)
    print("Common mode voltage: ", common_mode_voltage)


# Optionally pass URI as command line argument,

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
part_name = sys.argv[2].lower() if len(sys.argv) >= 3 else "adaq7768-1"

print(f"URI: {my_uri}")
print(f"Selected device: {part_name}")

# Initialize ADC depending on device name
if part_name == "ad7768-1":
    my_adc = adi.ad7768_1(uri=my_uri)
elif part_name == "adaq7767-1":
    my_adc = adi.adaq7767_1(uri=my_uri)
elif part_name == "adaq7768-1":
    my_adc = adi.adaq7768_1(uri=my_uri)
elif part_name == "adaq7769-1":
    my_adc = adi.adaq7769_1(uri=my_uri)
else:
    raise ValueError(f"Unsupported device: {part_name}")

my_adc = adi.ad7768_1(uri=my_uri)
my_adc.rx_buffer_size = 1024

my_adc.sampling_frequency = 8000  # Set Sample Rate

my_adc.rx_output_type = "SI"  # Choose output format: "SI" or "RAW"

my_adc.common_mode_voltage = "(AVDD1-AVSS)/2"  # mV # Set common mode voltage: (AVDD1-AVSS)/2 2V5 2V05 1V9 1V65 1V1 0V9 OFF

# Verify settings:
display_settings(
    my_adc.sampling_frequency, my_adc.rx_enabled_channels, my_adc.common_mode_voltage,
)

# --- Live Plot Setup ---
plt.ion()  # turn on interactive mode
fig, ax = plt.subplots(figsize=(10, 6))  # reasonable size for most monitors
(line,) = ax.plot([], [], label="voltage")
ax.set_xlabel("Data Point")
ax.set_ylabel("Millivolts" if my_adc.rx_output_type == "SI" else "ADC counts")
ax.legend(loc="upper right")
plt.show()

# --- Live Update Loop ---
try:
    while True:
        data = my_adc.rx()
        data = data[1:]  # skip first sample

        line.set_xdata(range(len(data)))
        line.set_ydata(data)

        ax.relim()
        ax.autoscale_view()

        plt.pause(0.01)

except KeyboardInterrupt:
    print("Stopped by user.")

del my_adc
