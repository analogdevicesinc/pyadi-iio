# ADPD410X demo python script for plotting

import sys
import time
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import adi

from typing import List

# Ensure connection to board
while True:
    port = input('Input Serial line (e.g. if ADICUP3029 is connected to COM7, input \'COM7\' )\nSerial line:')

    try:
        context = "serial:" + port + ",115200"
        adpd410x = adi.adpd410x(uri=context)
        print("\nADPD410X board detected.\nBegin setup query:\n")
        break
    except:
        print("Port not found\n")

# Get demo application to use
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

    def animate(i, xs, ys, zs):
        """Function called to animate in real time using SI"""
        global demoindex
        
        # Compute demo output and continuously adding data to the lists
        if demoindex==1:
            a1 = adpd410x.channel[0].raw
            a2 = adpd410x.channel[1].raw
            
            rrat = a1/a2
            quinine = (2.015e3)*(rrat**3) + (-1.609e2)*(rrat**2) + (4.681)*(rrat) + (9.385e-3)
            
            xs.append(quinine) # Fluorescence Data
        elif demoindex==2:
            a1 = adpd410x.channel[2].raw
            a2 = adpd410x.channel[3].raw
            
            rrat = a1/a2
            ph = (4.888e2)*(rrat**4) + (-1.018e3)*(rrat**3) + (7.392e2)*(rrat**2) + (-2.276e2)*(rrat) + (3.301e1)
            
            
            ys.append(ph) # Colorimetry Data
        elif demoindex==3:
            a1 = adpd410x.channel[6].raw
            a2 = adpd410x.channel[7].raw
            
            rrat = a1/a2
            turbidity = (1.666e4)*(rrat) + (0.833)
            
            if turbidity > 100:
                turbidity = (4.513e3)*(rrat) + (7.314e1)
            
            zs.append(turbidity) # Turbidity Data

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