#ADPD410X code to plot multiple channels at a time

import sys
import time
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import adi

from typing import List

#ensure connection to the board
while True:
    port = input('Input Serial line (e.g. if ADICUP3029 is connected to COM7, input \'COM7\' )\nSerial line:')

    try:
        context = "serial:" + port + ",115200"
        adpd410x = adi.adpd410x(uri=context)
        print("\nADPD410X board detected.\nBegin setup query:\n")
        break
    except:
        print("Port not found\n")

#get number of channels to plot
global raw
raw= []

global channelnum, channelcount
while True:
    channelcount = input('\nHow many channels to read? (1-8): ')
    try:
        channelcount = int(channelcount)
    except:
        print('Please input an integer within the specified range')
        continue
    if channelcount < 1 or channelcount > 8:
        print('Please input an integer within the specified range')
    else:
        break

channelindex: List[int] = [] #will handle channel indexes to be plotted

while True:
    channelnum = input('\nChoose channel number to read? (1-8): ')
    try:
        channelnum = int(channelnum)
    except:
        print('Please input an integer within the specified range')
        continue
    
    if channelnum < 1 or channelnum > 8:
        print('Please input an integer within the specified range')
    else:
        if len(channelindex) > 0:  #to check for repeated entries of channel number
            skip=0
            if channelnum in channelindex:
                skip=1
                print('This channel number is already entered. Please enter a different number.')
            if skip==0:   
                channelindex.append(channelnum)
                print(channelindex)
                channelcount=channelcount-1
        else:
            channelindex.append(channelnum)
            print(channelindex)
            channelcount=channelcount-1
    if channelcount < 1:
        break

# Set enable_plot to True if you want to plot in real-time
enable_plot = True

if enable_plot:

    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs: List[float] = [] #channel1
    ys: List[float] = [] #channel2
    zs: List[float] = [] #channel3
    bs: List[float] = [] #channel4
    cs: List[float] = [] #channel5
    ds: List[float] = [] #channel6
    es: List[float] = [] #channel7
    fs: List[float] = [] #channel8


    def animate(i, xs, ys, zs, bs, cs, ds, es, fs):
        """Function called to animate in real time using SI"""
        global channelindex

        # Continuously adding data from ADPD410X to lists
        xs.append(adpd410x.channel[0].raw) #channel1
        print(xs[-1])
        ys.append(adpd410x.channel[1].raw) #channel2
        print(ys[-1])
        zs.append(adpd410x.channel[2].raw) #channel3
        print(zs[-1])
        bs.append(adpd410x.channel[3].raw) #channel4
        print(bs[-1])
        cs.append(adpd410x.channel[4].raw) #channel5
        print(cs[-1])
        ds.append(adpd410x.channel[5].raw) #channel6
        print(ds[-1])
        es.append(adpd410x.channel[6].raw) #channel7
        print(es[-1])
        fs.append(adpd410x.channel[7].raw) #channel8
        print(fs[-1])

        # Limit channel lists to 200 items
        xs = xs[-200:]
        ys = ys[-200:]
        zs = zs[-200:]
        bs = bs[-200:]
        cs = cs[-200:]
        ds = ds[-200:]
        es = es[-200:]
        fs = fs[-200:]

        ax.clear()
        limits = []
        #Plotting desired channels
        for count in channelindex:
            if count==1:
                ax.plot(xs, label="ADPD410X Channel 1", linewidth=2.0)
                limits.extend([min(xs), max(xs)])
            if count==2:
                ax.plot(ys, label="ADPD410X Channel 2", linewidth=2.0)
                limits.extend([min(ys), max(ys)])
            if count==3:
                ax.plot(zs, label="ADPD410X Channel 3", linewidth=2.0)
                limits.extend([min(zs), max(zs)])
            if count==4:
                ax.plot(bs, label="ADPD410X Channel 4", linewidth=2.0)
                limits.extend([min(bs), max(bs)])
            if count==5:
                ax.plot(cs, label="ADPD410X Channel 5", linewidth=2.0)
                limits.extend([min(cs), max(cs)])
            if count==6:
                ax.plot(ds, label="ADPD410X Channel 6", linewidth=2.0)
                limits.extend([min(ds), max(ds)])
            if count==7:
                ax.plot(es, label="ADPD410X Channel 7", linewidth=2.0)
                limits.extend([min(es), max(es)])
            if count==8:
                ax.plot(fs, label="ADPD410X Channel 8", linewidth=2.0)
                limits.extend([min(fs), max(fs)])
        ax.set_ylim([min(limits)-5,max(limits)+5])

        # Format plot
        plt.title("ADPD410X Data Plot", fontweight="bold")
        plt.subplots_adjust(bottom=0.30)
        plt.tick_params(
            axis="x", which="both", bottom=True, top=False, labelbottom=False
        )
        plt.legend(
            bbox_to_anchor=[0.5, -0.1], ncol=2, loc="upper center", frameon=False
        )

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, zs, bs, cs, ds, es, fs), interval=10)
    plt.show()