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

import sys
import time
from typing import List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import adi

# Connect to user-provided serial port
while True:
    port = input('Input Serial line (e.g. if ADICUP3029 is connected to COM7, input \'COM7\' )\nSerial line:')

    try:
        context = "serial:" + port + ",115200"
        adpd410x = adi.adpd410x(uri=context)
        print("\nADPD410X board detected.\nBegin setup query:\n")
        break
    except:
        print("Port not found\n")

# Get number of channels to plot
while True:
    demoindex = input('\nPlease select a demo application? (1-4): \n[1] Fluorescence\n[2] pH\n[3] Turbidity\n')
    try:
        demoindex = int(demoindex)
    except:
        print('Please input an integer within the specified range')
        continue
    if demoindex < 1 or demoindex > 3:
        print('Please input an integer within the specified range')
    else:
        break

# Set enable_plot to True if you want to plot in real-time
enable_plot = True

if enable_plot:
    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs: List[float] = [] # Fluorescence Data
    ys: List[float] = [] # Colorimetry Data
    zs: List[float] = [] # Turbidity Data

    # Real-time plotting function
    def animate(i, xs, ys, zs):
        global demoindex
        
        # Compute demo output and continuously add data to the lists
        if demoindex==1:
            a1 = adpd410x.channel[0].raw
            a2 = adpd410x.channel[1].raw
            
            rrat = a1/a2
            quinine = (2.015e3)*(rrat**3) + (-1.609e2)*(rrat**2) + (4.681)*(rrat) + (9.385e-3)
            
            # Fluorescence Data
            xs.append(quinine)
            
        elif demoindex==2:
            a1 = adpd410x.channel[2].raw
            a2 = adpd410x.channel[3].raw
            
            rrat = a1/a2
            ph = (4.888e2)*(rrat**4) + (-1.018e3)*(rrat**3) + (7.392e2)*(rrat**2) + (-2.276e2)*(rrat) + (3.301e1)
            
            # Colorimetry Data
            ys.append(ph)
            
        elif demoindex==3:
            a1 = adpd410x.channel[6].raw
            a2 = adpd410x.channel[7].raw
            
            rrat = a1/a2
            turbidity = (1.666e4)*(rrat) + (0.833)
            
            if turbidity > 100:
                turbidity = (4.513e3)*(rrat) + (7.314e1)
            
            # Turbidity Data
            zs.append(turbidity)

        # Limit channel lists to 200 items
        xs = xs[-200:]
        ys = ys[-200:]
        zs = zs[-200:]

        ax.clear()
        limits = []
        
        #Plotting desired channels
        if demoindex==1:
            ax.plot(xs, label="Quinine Concentration (g/L) using Fluorescence", linewidth=2.0)
            ax.set_ylim([0, 0.1])
        elif demoindex==2:
            ax.plot(ys, label="pH using Colorimetry", linewidth=2.0)
            ax.set_ylim([0, 15])
        elif demoindex==3:
            ax.plot(zs, label="Turbidity (FTU)", linewidth=2.0)
            ax.set_ylim([0, 1000])

        # Format plot
        plt.title("ADPD410X Demo Data", fontweight="bold")
        plt.subplots_adjust(bottom=0.30)
        plt.tick_params(
            axis="x", which="both", bottom=True, top=False, labelbottom=False
        )
        plt.legend(
            bbox_to_anchor=[0.5, -0.1], ncol=2, loc="upper center", frameon=False
        )

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, zs), interval=25)
    plt.show()