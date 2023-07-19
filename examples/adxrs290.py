# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import List

import adi
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

# Set enable_plot to True if you want to plot in real-time
enable_plot = True

# Set up ADXRS290. Use correct URI.

# Use this with Raspberry Pi from a computer on the same network
# and make sure to use the correct IP of the  RPI.
# mygyro = adi.adxrs290(uri="ip:192.168.50.10")

# Use this with ADICUP3029 and make sure to use the correct com port.
mygyro = adi.adxrs290(uri="serial:COM26")

print("\nX Angular Velocity: " + str(mygyro.anglvel_x.raw))
print("Y Angular Velocity: " + str(mygyro.anglvel_y.raw))
print("Chip Temperature: " + str(mygyro.temp.raw))

# Setting and Reading the band pass filter
mygyro.hpf_3db_frequency = 0.000000
print("High pass filter 3D frequency: " + str(mygyro.hpf_3db_frequency))
mygyro.lpf_3db_frequency = 480.000000
print("Low pass filter 3D frequency: " + str(mygyro.lpf_3db_frequency))

# Read using RX.
mygyro.rx_output_type = "SI"
mygyro.rx_buffer_size = 10
mygyro.rx_enabled_channels = [0, 1]
print("\nData using unbuffered rx(), SI (rad/s):")
print(mygyro.rx())

mygyro.rx_output_type = "raw"
print("\nData using unbuffered rx(), raw:")
print(mygyro.rx())

if enable_plot:

    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs: List[float] = []
    ys: List[float] = []

    # Set output type to SI
    mygyro.rx_output_type = "SI"

    def animate(i, xs, ys):
        """Function called to animate in real time using SI"""

        # Getting unbuffered rx() data, SI
        # Continuously adding streams of x and y to lists
        xs.extend(mygyro.rx()[0])  # X Angular Velocity
        ys.extend(mygyro.rx()[1])  # Y Angular Velocity

        # Limit x and y lists to 200 items
        xs = xs[-200:]
        ys = ys[-200:]

        # Draw x and y lists
        ax.clear()
        ax.set_ylim([-5, 5])
        ax.plot(xs, label="X Angular Velocity", linewidth=2.0)
        ax.plot(ys, label="Y Angular Velocity", linewidth=2.0)

        # Format plot
        plt.title("ADXRS290 Angular Velocity Plot", fontweight="bold")
        plt.ylabel("Angular Velocity (rad/s)")
        plt.subplots_adjust(bottom=0.30)
        plt.tick_params(
            axis="x", which="both", bottom=True, top=False, labelbottom=False
        )
        plt.legend(
            bbox_to_anchor=[0.5, -0.1], ncol=2, loc="upper center", frameon=False
        )

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=10)
    plt.show()

del mygyro
