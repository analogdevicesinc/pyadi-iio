# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
from typing import List

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from adi.admt4000 import admt4000
from adi.context_manager import context_manager
import csv

# Set up ADMT4000. Use correct URI.

# Use correct URI. 
# Use IP address if connecting from a computer to the device via ethernet.
# User serial if connecting to a microcontroller via USB serial.
# iio_context = "ip:192.168.50.10"
iio_context = "serial:COM8,230400,8n1"

# Set enable_plot to True if you want to plot the results.
enable_plot = True

################################################################################
# Use this with MCUs running tinyiiod and make sure to use the correct com port.
dev = admt4000(uri=iio_context)

angle_scale = dev.angle.scale
temp_scale = dev.temp.scale
temp_offset = dev.temp.offset

curr_angle_raw = dev.angle.raw
curr_angle = (curr_angle_raw) * angle_scale
curr_temp_raw = dev.temp.raw
curr_temp = (curr_temp_raw + temp_offset) * temp_scale / 1000
print("ADMT4000 Current Readings")
print("Turn count: " + str(dev.turns.raw))
print("Angle: " + str(curr_angle_raw) + " (" + str(curr_angle) + " degrees)")
print("Temperature: " + str(curr_temp) + " C")

# Read using RX.
dev.rx_output_type = "SI"
print(dev.rx())
dev.rx_buffer_size = 20
dev.rx_enabled_channels = [0, 1]
if enable_plot:

    # Create figure for plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    turns: List[int] = []
    angle: List[float] = []

    def animate(i, turns, angle):
        """Function called to animate in real time with two data streams"""

        # Getting buffered rx() data, assuming it returns two streams
        try:
            admt_data = dev.rx()
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return
        # Continuously adding streams of data A and B to lists
        turns.extend(admt_data[0])
        angle.extend(admt_data[1])

        # Limit data lists to 200 items
        turns = turns[-200:]
        angle = angle[-200:]

        # Draw x and y lists for first subplot
        ax1.clear()
        ax1.set_ylim([-10, 60])
        ax1.plot(turns, label="Turns", linewidth=2.0, color='orange')
        ax1.text(0.02, 0.95, f"Turns: {turns[-1]}", transform=ax1.transAxes,)
        ax1.set_title("Turns")
        ax1.set_ylabel("Value")
        ax1.legend(loc="upper right")

        # Draw x and y lists for second subplot
        ax2.clear()
        ax2.set_ylim([0, 400])
        ax2.plot(angle, label="Angle", linewidth=2.0)
        ax2.text(0.02, 0.95, f"Angle: {angle[-1]:.4f} °", transform=ax2.transAxes,)
        ax2.set_title("Angle")
        ax2.set_ylabel("Value")
        ax2.legend(loc="upper right")

        # Format plot
        plt.subplots_adjust(hspace=0.4)

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(turns, angle), interval=100)
    plt.show()
del dev