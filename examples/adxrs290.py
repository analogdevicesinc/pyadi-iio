# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
mygyro.hpf_3db_frequency = 0.044000
print("High pass filter 3D frequency: " + str(mygyro.hpf_3db_frequency))
mygyro.lpf_3db_frequency = 160.000000
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
