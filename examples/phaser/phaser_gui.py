#!/usr/bin/env python3
#  Must use Python 3
# Copyright (C) 2022 Analog Devices, Inc.
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

import datetime
import os
import socket
import sys
import time
import tkinter as tk
import tkinter.messagebox as mb
import warnings
from tkinter import *
from tkinter import ttk

import adi
import matplotlib.pyplot as plt
import numpy as np
from ADAR_pyadi_functions import *  # import the ADAR1000 functions (These all start with ADAR_xxxx)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import Cursor
from phaser_functions import load_hb100_cal
from scipy import signal
from SDR_functions import *  # import the SDR functions (These all start with SDR_xxxx)

try:
    import config_custom as config  # this has all the key parameters that the user would want to change (i.e. calibration phase and antenna element spacing)

    print("Found custom config file")
except:
    print("Didn't find custom config, looking for default.")
    try:
        import config as config
    except:
        print("Make sure config.py is in this directory")
        sys.exit(0)

try:
    config.SignalFreq = load_hb100_cal()
    print("Found signal freq file, ", config.SignalFreq)
except:
    print("No signal freq found, keeping at ", config.SignalFreq)


# Figure out if we're running on the Raspberry Pi, indicated by a host name of "phaser".

if socket.gethostname().find(".") >= 0:
    my_hostname = socket.gethostname()
else:
    my_hostname = socket.gethostbyaddr(socket.gethostname())[0]

if "phaser" in my_hostname:  # See if we're running locally on Raspberry Pi
    rpi_ip = "ip:localhost"
    sdr_ip = "ip:192.168.2.1"  # Historical - assume default Pluto IP
    print("Hostname is phaser, connecting to ", rpi_ip, " and ", sdr_ip)

else:  # NOT running on the phaser, connect to phaser.local over network
    rpi_ip = "ip:phaser.local"  # IP address of the remote Raspberry Pi
    #     rpi_ip = "ip:169.254.225.48" # Hard code an IP here for debug
    # sdr_ip = "ip:pluto.local"  # Pluto IP, with modified IP address or not
    sdr_ip = "ip:phaser.local:50901"  # Context Forwarding in libiio 0.24!
    print("Hostname is NOT phaser, connecting to ", rpi_ip, " and ", sdr_ip)


gpios = adi.one_bit_adc_dac(rpi_ip)
gpios.gpio_vctrl_1 = 1  # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
gpios.gpio_vctrl_2 = (
    1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
)

# setup GPIOs to control if Tx is output on OUT1 or OUT2
gpios.gpio_div_mr = 1
gpios.gpio_div_s0 = 0
gpios.gpio_div_s1 = 0
gpios.gpio_div_s2 = 0
gpios.gpio_tx_sw = 0  # gpio_tx_sw is "gpio_w" on schematic.  0=OUT1, 1=OUT2
time.sleep(0.5)


class App:
    def __init__(self, master):
        """SET DEFAULT VALUES"""
        self.time0 = datetime.datetime.now()
        self.sdr_address = sdr_ip
        self.SignalFreq = config.SignalFreq
        self.Tx_freq = config.Tx_freq  # Pluto's Tx LO freq.
        self.Rx_freq = config.Rx_freq  # Pluto's Rx LO freq
        self.LO_freq = self.SignalFreq + self.Rx_freq  # freq of the LTC5548 mixer LO
        self.SampleRate = config.SampleRate
        self.Rx_gain = config.Rx_gain
        self.Tx_gain = config.Tx_gain
        self.Averages = config.Averages
        self.RxGain1 = 100
        self.RxGain2 = 100
        self.RxGain3 = 100
        self.RxGain4 = 100
        self.RxGain5 = 100
        self.RxGain6 = 100
        self.RxGain7 = 100
        self.RxGain8 = 100
        self.Rx1_cal = config.Rx1_cal
        self.Rx2_cal = config.Rx2_cal
        self.Rx3_cal = config.Rx3_cal
        self.Rx4_cal = config.Rx4_cal
        self.Rx5_cal = config.Rx5_cal
        self.Rx6_cal = config.Rx6_cal
        self.Rx7_cal = config.Rx7_cal
        self.Rx8_cal = config.Rx8_cal
        self.refresh_time = config.refresh_time
        self.c = 299792458  # speed of light in m/s
        self.d = config.d
        self.saved_gain = []
        self.saved_angle = []
        self.saved_gainB = []
        self.saved_angleB = []
        self.ArrayGain = []
        self.ArrayAngle = []
        self.ArrayError = []
        self.ArrayBeamPhase = []
        self.TrackArray = []
        self.Gain_time = [-100] * 100
        self.win_width = 0
        self.win_height = 0
        for i in range(0, 1000):
            self.TrackArray.append(0)  # array of zeros
        self.max_hold = -1000
        self.min_hold = 1000
        """Initialize Pluto"""
        self.sdr = SDR_init(
            self.sdr_address,
            self.SampleRate,
            self.Tx_freq,
            self.Rx_freq,
            self.Rx_gain,
            self.Tx_gain,
            config.buffer_size,
        )
        SDR_LO_init(rpi_ip, self.LO_freq)

        """Initialize the ADAR1000"""
        time.sleep(0.5)
        self.array = adi.adar1000_array(
            uri=rpi_ip,
            chip_ids=[
                "BEAM0",
                "BEAM1",
            ],  # these are the ADAR1000s' labels in the device tree
            device_map=[[1], [2]],
            element_map=[[1, 2, 3, 4, 5, 6, 7, 8]],
            device_element_map={
                1: [7, 8, 5, 6],  # i.e. channel2 of device1 (BEAM0), maps to element 8
                2: [3, 4, 1, 2],
            },
        )
        for device in self.array.devices.values():
            ADAR_init(
                device
            )  # resets the ADAR1000, then reprograms it to the standard config
            ADAR_set_mode(
                device, "rx"
            )  # configures for rx or tx.  And sets the LNAs for Receive mode or the PA's for Transmit mode
        gainList = [
            self.RxGain1,
            self.RxGain2,
            self.RxGain3,
            self.RxGain4,
            self.RxGain5,
            self.RxGain6,
            self.RxGain7,
            self.RxGain8,
        ]
        ADAR_set_Taper(self.array, gainList)

        master.protocol(
            "WM_DELETE_WINDOW", self.closeProgram
        )  # clicking the "x" button to close the window will shut things down properly (using the closeProgram method)
        self.master = master

        """BUILD THE GUI: Master Frame"""
        self.refresh = tk.IntVar()
        check_refresh = tk.Checkbutton(
            self.master,
            text="Auto Refresh Data",
            highlightthickness=0,
            variable=self.refresh,
            command=self.updater,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=FLAT,
        )
        check_refresh.grid(row=14, column=0, columnspan=2, sticky=E + W)
        self.refresh.set(0)
        b1 = Button(self.master, text="Acquire Data", command=self.updater)
        b1.grid(row=14, column=2, columnspan=2, sticky=E + W)
        button_exit = Button(
            self.master,
            text="Close Program",
            command=self.closeProgram,
            bd=4,
            bg="LightYellow3",
            relief=RAISED,
        )
        button_save = Button(
            self.master, text="Copy Plot A", fg="green", command=self.savePlot
        )
        button_save.grid(row=14, column=5, columnspan=1, sticky=E + W)
        button_save2 = Button(
            self.master, text="Copy Plot B", fg="purple", command=self.savePlotB
        )
        button_save2.grid(row=14, column=6, columnspan=1, sticky=E + W)
        button_clear = Button(self.master, text="Clear Memory", command=self.clearPlot)
        button_clear.grid(row=14, column=7, columnspan=1, sticky=E + W)
        button_exit.grid(row=14, column=8, columnspan=1, padx=50, pady=10, sticky=E + W)

        cntrl_width = 450
        cntrl_height = 600
        cntrl_tabs = ttk.Notebook(self.master, height=cntrl_height, width=cntrl_width)
        cntrl_tabs.grid(padx=10, pady=10, row=0, column=0, columnspan=4, sticky=N)
        frame1 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame2 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame3 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame4 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame5 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame6 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame7 = Frame(cntrl_tabs, width=cntrl_width, height=cntrl_height)
        frame1.grid(row=0, column=0)
        frame2.grid(row=0, column=1)
        frame3.grid(row=0, column=1)
        frame4.grid(row=0, column=1)
        frame5.grid(row=0, column=1)
        frame6.grid(row=0, column=1)
        frame7.grid(row=0, column=1)
        cntrl_tabs.add(frame1, text="Config")
        cntrl_tabs.add(frame2, text="Gain")
        cntrl_tabs.add(frame3, text="Phase")
        cntrl_tabs.add(frame4, text="BW")
        cntrl_tabs.add(frame5, text="Bits")
        cntrl_tabs.add(frame6, text="Digital")
        cntrl_tabs.add(frame7, text="Plot Options")
        """Frame1:  Config"""

        def Tx_mode_select(value):
            if value == "Transmit on OUT1":
                gpios.gpio_tx_sw = (
                    0  # gpio_tx_sw is "gpio_w" on schematic.  0=OUT1, 1=OUT2
                )
                gpios.gpio_vctrl_2 = 1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
                slide_TxGain.config(state=ACTIVE, troughcolor="LightYellow3")
                slide_TxGain.set(config.Tx_gain)
            elif value == "Transmit on OUT2":
                gpios.gpio_tx_sw = (
                    1  # gpio_tx_sw is "gpio_w" on schematic.  0=OUT1, 1=OUT2
                )
                gpios.gpio_vctrl_2 = 1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
                slide_TxGain.config(state=ACTIVE, troughcolor="LightYellow3")
                slide_TxGain.set(config.Tx_gain)
            else:
                gpios.gpio_vctrl_2 = 1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
                slide_TxGain.set(-80)
                slide_TxGain.config(state=DISABLED, troughcolor="light gray")

        self.freq = tk.DoubleVar()
        self.RxGain = tk.DoubleVar()
        self.TxGain = tk.DoubleVar()
        self.Tx_select = StringVar()
        self.Tx_select.set("Transmit Disabled")
        slide_SignalFreq = Scale(
            frame1,
            from_=9.5,
            to=11,
            variable=self.freq,
            resolution=0.001,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_RxGain = Scale(
            frame1,
            from_=0,
            to=60,
            resolution=1,
            variable=self.RxGain,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_TxGain = Scale(
            frame1,
            from_=-80,
            to=-3,
            resolution=1,
            variable=self.TxGain,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        Tx_sel_menu = OptionMenu(
            frame1,
            self.Tx_select,
            "Transmit on OUT1",
            "Transmit on OUT2",
            "Transmit Disabled",
            command=Tx_mode_select,
        )
        Tx_sel_menu.grid(
            row=9, column=0, padx=100, pady=2, rowspan=3, columnspan=3, sticky=E + W
        )
        # slide_Average=Scale(frame1, from_=1, to=20, resolution=1, variable=self.Avg, troughcolor="LightYellow3", bd=2, orient=HORIZONTAL, relief=SUNKEN, length=200)
        slide_SignalFreq.grid(row=0, column=0, padx=10, pady=10, rowspan=3)
        slide_RxGain.grid(row=3, column=0, padx=10, pady=10, rowspan=3)
        slide_TxGain.grid(row=6, column=0, padx=10, pady=10, rowspan=3)
        # slide_Average.grid(row=9, column=0, padx=10, pady=10, rowspan=3)
        slide_SignalFreq.set(self.SignalFreq / 1e9)
        slide_RxGain.set(int(self.Rx_gain))
        slide_TxGain.set(int(self.Tx_gain))
        Tx_mode_select(self.Tx_select)
        tk.Label(frame1, text="Signal Freq (GHz)", relief=SUNKEN, anchor=W).grid(
            row=1, column=2, sticky=E + W
        )
        tk.Label(frame1, text="Rx Gain (dB)", relief=SUNKEN, anchor=W).grid(
            row=4, column=2, sticky=E + W
        )
        tk.Label(frame1, text="Tx Gain (dB)", relief=SUNKEN, anchor=W).grid(
            row=7, column=2, sticky=E + W
        )
        # tk.Label(frame1, text="Times to Average", relief=SUNKEN, anchor=W).grid(row=10, column=2, sticky=E+W)
        self.update_time = tk.IntVar()
        slide_refresh_time = Scale(
            frame1,
            from_=0,
            to=1000,
            variable=self.update_time,
            resolution=50,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_refresh_time.grid(row=16, column=0, padx=10, pady=10, rowspan=3)
        tk.Label(frame1, text="Wait Time (ms)", relief=SUNKEN, anchor=W).grid(
            row=17, column=2, pady=20, sticky=E + W
        )
        self.update_time.set(self.refresh_time)

        # self.Divider = tk.Label(frame1, relief=SUNKEN, anchor=W).grid(row=18, column=0, columnspan=3, pady=10, padx=5, sticky=E+W)
        self.RxPhaseDelta = tk.DoubleVar()
        slide_RxPhaseDelta = Scale(
            frame1,
            from_=-75,
            to=75,
            resolution=1,
            digits=2,
            variable=self.RxPhaseDelta,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_RxPhaseDelta.grid(row=23, column=0, padx=10, pady=10, rowspan=3)
        slide_RxPhaseDelta.set(0)

        self.PhaseLabel_text = tk.StringVar()
        self.PhaseVal_text = tk.StringVar()
        self.label_phase = tk.Label(
            frame1, textvariable=self.PhaseLabel_text, anchor=W
        ).grid(row=26, column=0, columnspan=3, pady=10, padx=2, sticky=E + W)
        self.PhaseVal_label = tk.Label(
            frame1, textvariable=self.PhaseVal_text, anchor=W
        ).grid(row=27, column=0, columnspan=3, pady=2, padx=2, sticky=E + W)
        self.PhaseLabel_text.set("")

        def zero_PhaseDelta():
            slide_RxPhaseDelta.set(0)

        static_phase_label = tk.Button(
            frame1,
            text="Steering Angle",
            relief=RAISED,
            anchor=W,
            command=zero_PhaseDelta,
            highlightthickness=0,
        )
        static_phase_label.grid(row=24, column=2, sticky=E + W)
        self.PhaseVal_text.set("")

        def mode_select(value):
            if value == "Signal vs Time":
                print("Plotting Signal vs Time")
                self.plot_tabs.add(self.frame15)  # Signal Tracking Plot
                self.plot_tabs.select(4)
                self.Gain_time = [-100] * 100
            if value == "Static Phase" or value == "Signal vs Time":
                slide_RxPhaseDelta.grid()
                static_phase_label.grid()
                self.PhaseLabel_text.set("Element 1-8 Phase Values: ")
                self.PhaseVal_text.set("El 1-8 Phase Values: ")
            else:
                slide_RxPhaseDelta.grid_remove()
                static_phase_label.grid_remove()
                self.PhaseLabel_text.set("")
                self.PhaseVal_text.set("")
            if value == "Tracking":
                self.plot_tabs.select(3)
                self.find_peak()
            else:
                self.updater()

        self.mode_var = StringVar()
        self.mode_var.set("Beam Sweep")
        slide_RxPhaseDelta.grid_remove()
        static_phase_label.grid_remove()
        mode_Menu = OptionMenu(
            frame1,
            self.mode_var,
            "Beam Sweep",
            "Static Phase",
            "Signal vs Time",
            "Tracking",
            command=mode_select,
        )
        mode_Menu.grid(row=19, column=0, padx=10, pady=10, rowspan=1, sticky=E + W)
        tk.Label(frame1, text="Mode Selection", relief=SUNKEN, anchor=W).grid(
            row=19, column=2, pady=20, sticky=E + W
        )

        """Frame2:  Gain"""
        self.Rx1Gain_set = tk.IntVar()
        self.Rx2Gain_set = tk.IntVar()
        self.Rx3Gain_set = tk.IntVar()
        self.Rx4Gain_set = tk.IntVar()
        self.Rx5Gain_set = tk.IntVar()
        self.Rx6Gain_set = tk.IntVar()
        self.Rx7Gain_set = tk.IntVar()
        self.Rx8Gain_set = tk.IntVar()
        self.Sym_set = tk.IntVar()
        self.Sym_set = 0

        def sym_Rx1(val):
            if self.Sym_set.get() == 1:
                slide_Rx8Gain.configure(state="normal")
                slide_Rx8Gain.set(val)
                slide_Rx8Gain.configure(state="disabled")

        def sym_Rx2(val):
            if self.Sym_set.get() == 1:
                slide_Rx7Gain.configure(state="normal")
                slide_Rx7Gain.set(val)
                slide_Rx7Gain.configure(state="disabled")

        def sym_Rx3(val):
            if self.Sym_set.get() == 1:
                slide_Rx6Gain.configure(state="normal")
                slide_Rx6Gain.set(val)
                slide_Rx6Gain.configure(state="disabled")

        def sym_Rx4(val):
            if self.Sym_set.get() == 1:
                slide_Rx5Gain.configure(state="normal")
                slide_Rx5Gain.set(val)
                slide_Rx5Gain.configure(state="disabled")

        slide_Rx1Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx1Gain_set,
            command=sym_Rx1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx2Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx2Gain_set,
            command=sym_Rx2,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx3Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx3Gain_set,
            command=sym_Rx3,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx4Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx4Gain_set,
            command=sym_Rx4,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx5Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx5Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx6Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx6Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx7Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx7Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx8Gain = Scale(
            frame2,
            from_=0,
            to=100,
            resolution=1,
            variable=self.Rx8Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )

        slide_Rx1Gain.grid(row=0, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx2Gain.grid(row=3, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx3Gain.grid(row=6, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx4Gain.grid(row=9, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx5Gain.grid(row=12, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx6Gain.grid(row=15, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx7Gain.grid(row=18, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx8Gain.grid(row=21, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_Rx1Gain.set(100)
        slide_Rx2Gain.set(100)
        slide_Rx3Gain.set(100)
        slide_Rx4Gain.set(100)
        slide_Rx5Gain.set(100)
        slide_Rx6Gain.set(100)
        slide_Rx7Gain.set(100)
        slide_Rx8Gain.set(100)

        def Rx1_toggle():
            if slide_Rx1Gain.get() == 0:
                slide_Rx1Gain.set(100)
            else:
                slide_Rx1Gain.set(0)

        def Rx2_toggle():
            if slide_Rx2Gain.get() == 0:
                slide_Rx2Gain.set(100)
            else:
                slide_Rx2Gain.set(0)

        def Rx3_toggle():
            if slide_Rx3Gain.get() == 0:
                slide_Rx3Gain.set(100)
            else:
                slide_Rx3Gain.set(0)

        def Rx4_toggle():
            if slide_Rx4Gain.get() == 0:
                slide_Rx4Gain.set(100)
            else:
                slide_Rx4Gain.set(0)

        def Rx5_toggle():
            if slide_Rx5Gain.get() == 0:
                slide_Rx5Gain.set(100)
            else:
                slide_Rx5Gain.set(0)

        def Rx6_toggle():
            if slide_Rx6Gain.get() == 0:
                slide_Rx6Gain.set(100)
            else:
                slide_Rx6Gain.set(0)

        def Rx7_toggle():
            if slide_Rx7Gain.get() == 0:
                slide_Rx7Gain.set(100)
            else:
                slide_Rx7Gain.set(0)

        def Rx8_toggle():
            if slide_Rx8Gain.get() == 0:
                slide_Rx8Gain.set(100)
            else:
                slide_Rx8Gain.set(0)

        tk.Button(
            frame2,
            text="Rx1 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx1_toggle,
            highlightthickness=0,
        ).grid(row=1, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx2 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx2_toggle,
            highlightthickness=0,
        ).grid(row=4, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx3 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx3_toggle,
            highlightthickness=0,
        ).grid(row=7, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx4 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx4_toggle,
            highlightthickness=0,
        ).grid(row=10, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx5 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx5_toggle,
            highlightthickness=0,
        ).grid(row=13, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx6 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx6_toggle,
            highlightthickness=0,
        ).grid(row=16, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx7 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx7_toggle,
            highlightthickness=0,
        ).grid(row=19, column=3, sticky=E + W)
        tk.Button(
            frame2,
            text="Rx8 Gain (%)",
            relief=RAISED,
            anchor=W,
            command=Rx8_toggle,
            highlightthickness=0,
        ).grid(row=22, column=3, sticky=E + W)

        def sym_sel():
            if self.Sym_set.get() == 1:
                slide_Rx5Gain.configure(state="normal")  # 'normal'
                slide_Rx6Gain.configure(state="normal")  # 'normal'
                slide_Rx7Gain.configure(state="normal")  # 'normal'
                slide_Rx8Gain.configure(state="normal")  # 'normal'
                slide_Rx5Gain.set(self.Rx4Gain_set.get())
                slide_Rx6Gain.set(self.Rx3Gain_set.get())
                slide_Rx7Gain.set(self.Rx2Gain_set.get())
                slide_Rx8Gain.set(self.Rx1Gain_set.get())
                slide_Rx5Gain.configure(state="disabled")  # 'normal'
                slide_Rx6Gain.configure(state="disabled")  # 'normal'
                slide_Rx7Gain.configure(state="disabled")  # 'normal'
                slide_Rx8Gain.configure(state="disabled")  # 'normal'
            if self.Sym_set.get() == 0:
                slide_Rx5Gain.configure(state="normal")  # 'disabled'
                slide_Rx6Gain.configure(state="normal")  # 'disabled'
                slide_Rx7Gain.configure(state="normal")  # 'disabled'
                slide_Rx8Gain.configure(state="normal")  # 'disabled'

        self.Sym_set = tk.IntVar()
        check_Sym = tk.Checkbutton(
            frame2,
            text="Symmetric Taper",
            highlightthickness=0,
            variable=self.Sym_set,
            onvalue=1,
            offvalue=0,
            command=sym_sel,
            relief=SUNKEN,
            anchor=W,
        )
        check_Sym.grid(row=24, column=0, columnspan=2, padx=5, pady=5, sticky=E + W)

        def taper_profile(taper_var):
            if taper_var == 1:  # Rect Window
                gain1 = 100
                gain2 = 100
                gain3 = 100
                gain4 = 100
            elif taper_var == 2:  # Chebyshev
                gain1 = 4
                gain2 = 23
                gain3 = 62
                gain4 = 100
            elif taper_var == 3:  # Hamming
                gain1 = 9
                gain2 = 27
                gain3 = 67
                gain4 = 100
            elif taper_var == 4:  # Hann
                gain1 = 12
                gain2 = 43
                gain3 = 77
                gain4 = 100
            elif taper_var == 5:  # Blackman
                gain1 = 6
                gain2 = 27
                gain3 = 66
                gain4 = 100
            slide_Rx1Gain.configure(state="normal")  # 'disabled'
            slide_Rx2Gain.configure(state="normal")  # 'disabled'
            slide_Rx3Gain.configure(state="normal")  # 'disabled'
            slide_Rx4Gain.configure(state="normal")  # 'disabled'
            slide_Rx5Gain.configure(state="normal")  # 'disabled'
            slide_Rx6Gain.configure(state="normal")  # 'disabled'
            slide_Rx7Gain.configure(state="normal")  # 'disabled'
            slide_Rx8Gain.configure(state="normal")  # 'disabled'
            slide_Rx1Gain.set(gain1)
            slide_Rx2Gain.set(gain2)
            slide_Rx3Gain.set(gain3)
            slide_Rx4Gain.set(gain4)
            slide_Rx5Gain.set(gain4)
            slide_Rx6Gain.set(gain3)
            slide_Rx7Gain.set(gain2)
            slide_Rx8Gain.set(gain1)

        button_rect = Button(
            frame2, text="Rect Window", command=lambda: taper_profile(1)
        )
        button_rect.grid(row=25, column=0, columnspan=1, padx=2, pady=1, sticky=E + W)
        button_cheb = Button(frame2, text="Chebyshev", command=lambda: taper_profile(2))
        button_cheb.grid(row=25, column=1, columnspan=1, padx=2, pady=1, sticky=E + W)
        # button_hamming = Button(frame2, text="Hamming", command=lambda: taper_profile(3))
        # button_hamming.grid(row=25, column=2, columnspan=1, padx=2, pady=1, sticky=E+W)
        button_hann = Button(frame2, text="Hann", command=lambda: taper_profile(4))
        button_hann.grid(row=26, column=0, columnspan=1, padx=2, pady=1, sticky=E + W)
        button_black = Button(frame2, text="Blackman", command=lambda: taper_profile(5))
        button_black.grid(row=26, column=1, columnspan=1, padx=2, pady=1, sticky=E + W)
        """Frame3:  Phase"""
        self.Rx1Phase_set = tk.DoubleVar()
        self.Rx2Phase_set = tk.DoubleVar()
        self.Rx3Phase_set = tk.DoubleVar()
        self.Rx4Phase_set = tk.DoubleVar()
        self.Rx5Phase_set = tk.DoubleVar()
        self.Rx6Phase_set = tk.DoubleVar()
        self.Rx7Phase_set = tk.DoubleVar()
        self.Rx8Phase_set = tk.DoubleVar()
        slide_Rx1Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx1Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx2Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx2Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx3Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx3Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx4Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx4Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx1Phase.grid(row=0, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_Rx2Phase.grid(row=3, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_Rx3Phase.grid(row=6, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_Rx4Phase.grid(row=9, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_Rx1Phase.set(0)
        slide_Rx2Phase.set(0)
        slide_Rx3Phase.set(0)
        slide_Rx4Phase.set(0)

        def zero_Rx1():
            slide_Rx1Phase.set(0)

        def zero_Rx2():
            slide_Rx2Phase.set(0)

        def zero_Rx3():
            slide_Rx3Phase.set(0)

        def zero_Rx4():
            slide_Rx4Phase.set(0)

        def zero_Rx5():
            slide_Rx5Phase.set(0)

        def zero_Rx6():
            slide_Rx6Phase.set(0)

        def zero_Rx7():
            slide_Rx7Phase.set(0)

        def zero_Rx8():
            slide_Rx8Phase.set(0)

        tk.Button(
            frame3,
            text="Rx1 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx1,
            highlightthickness=0,
        ).grid(row=1, column=3, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx2 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx2,
            highlightthickness=0,
        ).grid(row=4, column=3, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx3 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx3,
            highlightthickness=0,
        ).grid(row=7, column=3, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx4 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx4,
            highlightthickness=0,
        ).grid(row=10, column=3, sticky=E + W)
        Phase_set = tk.IntVar()

        def phase_sel():
            global phase1
            global phase2
            global phase3
            global phase4
            global phase5
            global phase6
            global phase7
            global phase8
            if Phase_set.get() == 1:
                phase1 = slide_Rx1Phase.get()
                phase2 = slide_Rx2Phase.get()
                phase3 = slide_Rx3Phase.get()
                phase4 = slide_Rx4Phase.get()
                phase5 = slide_Rx5Phase.get()
                phase6 = slide_Rx6Phase.get()
                phase7 = slide_Rx7Phase.get()
                phase8 = slide_Rx8Phase.get()
                slide_Rx1Phase.set(0)
                slide_Rx2Phase.set(0)
                slide_Rx3Phase.set(0)
                slide_Rx4Phase.set(0)
                slide_Rx5Phase.set(0)
                slide_Rx6Phase.set(0)
                slide_Rx7Phase.set(0)
                slide_Rx8Phase.set(0)
                slide_Rx1Phase.configure(state="disabled")  # 'normal'
                slide_Rx2Phase.configure(state="disabled")  # 'normal'
                slide_Rx3Phase.configure(state="disabled")  # 'normal'
                slide_Rx4Phase.configure(state="disabled")  # 'normal'
                slide_Rx5Phase.configure(state="disabled")  # 'normal'
                slide_Rx6Phase.configure(state="disabled")  # 'normal'
                slide_Rx7Phase.configure(state="disabled")  # 'normal'
                slide_Rx8Phase.configure(state="disabled")  # 'normal'
            else:
                slide_Rx1Phase.configure(state="normal")  # 'disabled'
                slide_Rx2Phase.configure(state="normal")  # 'disabled'
                slide_Rx3Phase.configure(state="normal")  # 'disabled'
                slide_Rx4Phase.configure(state="normal")  # 'disabled'
                slide_Rx5Phase.configure(state="normal")  # 'disabled'
                slide_Rx6Phase.configure(state="normal")  # 'disabled'
                slide_Rx7Phase.configure(state="normal")  # 'disabled'
                slide_Rx8Phase.configure(state="normal")  # 'disabled'
                slide_Rx1Phase.set(phase1)
                slide_Rx2Phase.set(phase2)
                slide_Rx3Phase.set(phase3)
                slide_Rx4Phase.set(phase4)
                slide_Rx5Phase.set(phase5)
                slide_Rx6Phase.set(phase6)
                slide_Rx7Phase.set(phase7)
                slide_Rx8Phase.set(phase8)

        check_Phase = tk.Checkbutton(
            frame3,
            text="Set All Phase to 0",
            variable=Phase_set,
            highlightthickness=0,
            onvalue=1,
            offvalue=0,
            command=phase_sel,
            anchor=W,
            relief=SUNKEN,
        )
        check_Phase.grid(row=24, column=0, padx=10, pady=10, sticky=E + W)
        slide_Rx5Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx5Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx6Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx6Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx7Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx7Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx8Phase = Scale(
            frame3,
            from_=-180,
            to=180,
            resolution=2.8125,
            digits=7,
            variable=self.Rx8Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_Rx5Phase.grid(
            row=12, column=0, padx=2, pady=2, columnspan=3, rowspan=3, sticky=E + W
        )
        slide_Rx6Phase.grid(
            row=15, column=0, padx=2, pady=2, columnspan=3, rowspan=3, sticky=E + W
        )
        slide_Rx7Phase.grid(
            row=18, column=0, padx=2, pady=2, columnspan=3, rowspan=3, sticky=E + W
        )
        slide_Rx8Phase.grid(
            row=21, column=0, padx=2, pady=2, columnspan=3, rowspan=3, sticky=E + W
        )
        slide_Rx5Phase.set(0)
        slide_Rx6Phase.set(0)
        slide_Rx7Phase.set(0)
        slide_Rx8Phase.set(0)
        tk.Button(
            frame3,
            text="Rx5 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx5,
            highlightthickness=0,
        ).grid(row=13, column=3, padx=1, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx6 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx6,
            highlightthickness=0,
        ).grid(row=16, column=3, padx=1, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx7 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx7,
            highlightthickness=0,
        ).grid(row=19, column=3, padx=1, sticky=E + W)
        tk.Button(
            frame3,
            text="Rx8 Phase",
            relief=RAISED,
            anchor=W,
            command=zero_Rx8,
            highlightthickness=0,
        ).grid(row=22, column=3, padx=1, sticky=E + W)
        """Frame4:  BW"""
        self.BW = tk.DoubleVar()
        slide_SignalBW = Scale(
            frame4,
            from_=0,
            to=2000,
            variable=self.BW,
            resolution=100,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_SignalBW.grid(row=0, column=0, padx=10, pady=10, rowspan=3)
        slide_SignalBW.set(self.SignalFreq / 1e9)
        tk.Label(frame4, text="Signal BW (MHz)", relief=SUNKEN, anchor=W).grid(
            row=1, column=2, sticky=E + W
        )
        self.RxSignal_text = tk.StringVar()
        self.RxSignal = tk.Label(
            frame4, textvariable=self.RxSignal_text, relief=SUNKEN, anchor=W
        ).grid(row=8, column=0, pady=10, padx=5, sticky=E + W)
        self.RxSignal_text.set("Signal Bandwidth = ")
        self.MixerLO_text = tk.StringVar()
        self.MixerLO = tk.Label(
            frame4, textvariable=self.MixerLO_text, relief=SUNKEN, anchor=W
        ).grid(row=9, column=0, pady=10, padx=5, sticky=E + W)
        self.MixerLO_text.set("Mixer LO Freq = ")
        self.PlutoRxLO_text = tk.StringVar()
        self.PlutoRxLO = tk.Label(
            frame4, textvariable=self.PlutoRxLO_text, relief=SUNKEN, anchor=W
        ).grid(row=10, column=0, pady=10, padx=5, sticky=E + W)
        self.PlutoRxLO_text.set("Pluto Rx LO = ")
        self.BeamCalc_text = tk.StringVar()
        self.BeamCalc = tk.Label(
            frame4, textvariable=self.BeamCalc_text, relief=SUNKEN, anchor=W
        ).grid(row=11, column=0, pady=10, padx=5, sticky=E + W)
        self.BeamCalc_text.set("Beam Calculated at ")
        self.AngleMeas_text = tk.StringVar()
        self.AngleMeas = tk.Label(
            frame4, textvariable=self.AngleMeas_text, relief=SUNKEN, anchor=W
        ).grid(row=12, column=0, pady=10, padx=5, sticky=E + W)
        self.AngleMeas_text.set("Beam Measured at ")
        """Frame5:  Bits"""
        self.res = tk.DoubleVar()
        self.bits = tk.IntVar()
        slide_res = Scale(
            frame5,
            from_=0.1,
            to=5,
            variable=self.res,
            resolution=0.1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_bits = Scale(
            frame5,
            from_=1,
            to=7,
            resolution=1,
            variable=self.bits,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_res.grid(row=0, column=0, padx=10, pady=10, rowspan=3)
        slide_bits.grid(row=3, column=0, padx=10, pady=10, rowspan=3)
        slide_res.set(2.8125)
        slide_bits.set(7)
        tk.Label(frame5, text="Steer Resolution", relief=SUNKEN, anchor=W).grid(
            row=1, column=2, sticky=E + W
        )
        tk.Label(frame5, text="Phase Shift Bits", relief=SUNKEN, anchor=W).grid(
            row=4, column=2, sticky=E + W
        )
        self.res_text = tk.StringVar()
        self.res_degrees = tk.Label(
            frame5, textvariable=self.res_text, relief=SUNKEN, anchor=W
        ).grid(row=8, column=0, columnspan=3, pady=10, padx=5, sticky=E + W)
        self.res_text.set("Phase Shift Steps = ")
        self.res_bits = tk.IntVar()
        check_res_bits = tk.Checkbutton(
            frame5,
            text="Ignore Steer Res",
            highlightthickness=0,
            variable=self.res_bits,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=FLAT,
        )
        check_res_bits.grid(row=10, column=0, columnspan=1, sticky=E + W)
        self.res_bits.set(1)
        """Frame6:  Digital Controls"""
        self.Beam0_Phase_set = tk.DoubleVar()
        self.Beam1_Phase_set = tk.DoubleVar()
        slide_B0_Phase = Scale(
            frame6,
            from_=-180,
            to=180,
            resolution=1,
            digits=3,
            variable=self.Beam0_Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_B1_Phase = Scale(
            frame6,
            from_=-180,
            to=180,
            resolution=1,
            digits=3,
            variable=self.Beam1_Phase_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_B0_Phase.grid(row=0, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_B1_Phase.grid(row=3, column=0, padx=2, pady=2, columnspan=3, rowspan=3)
        slide_B0_Phase.set(0)
        slide_B1_Phase.set(0)

        def zero_B0_phase():
            slide_B0_Phase.set(0)

        def zero_B1_phase():
            slide_B1_Phase.set(0)

        tk.Button(
            frame6,
            text="Beam0 Phase Shift",
            relief=RAISED,
            anchor=W,
            command=zero_B0_phase,
            highlightthickness=0,
        ).grid(row=1, column=3, sticky=E + W)
        tk.Button(
            frame6,
            text="Beam1 Phase Shift",
            relief=RAISED,
            anchor=W,
            command=zero_B1_phase,
            highlightthickness=0,
        ).grid(row=4, column=3, sticky=E + W)

        self.B0_Gain_set = tk.DoubleVar()
        self.B1_Gain_set = tk.DoubleVar()
        slide_B0_Gain = Scale(
            frame6,
            from_=0,
            to=2,
            resolution=0.1,
            variable=self.B0_Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_B1_Gain = Scale(
            frame6,
            from_=0,
            to=2,
            resolution=0.1,
            variable=self.B1_Gain_set,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_B0_Gain.grid(row=12, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_B1_Gain.grid(row=15, column=0, padx=2, pady=2, rowspan=3, columnspan=3)
        slide_B0_Gain.set(1)
        slide_B1_Gain.set(1)

        def B0_toggle():
            if slide_B0_Gain.get() == 0:
                slide_B0_Gain.set(1)
            else:
                slide_B0_Gain.set(0)

        def B1_toggle():
            if slide_B1_Gain.get() == 0:
                slide_B1_Gain.set(1)
            else:
                slide_B1_Gain.set(0)

        tk.Button(
            frame6,
            text="Beam0 Gain",
            relief=RAISED,
            anchor=W,
            command=B0_toggle,
            highlightthickness=0,
        ).grid(row=13, column=3, sticky=E + W)
        tk.Button(
            frame6,
            text="Beam1 Gain",
            relief=RAISED,
            anchor=W,
            command=B1_toggle,
            highlightthickness=0,
        ).grid(row=16, column=3, sticky=E + W)

        self.show_delta = tk.IntVar()
        check_delta = tk.Checkbutton(
            frame6,
            text="Show Delta",
            highlightthickness=0,
            variable=self.show_delta,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=SUNKEN,
        )
        check_delta.grid(row=21, column=0, columnspan=3, padx=5, pady=15, sticky=E + W)
        self.show_delta.set(0)
        self.show_error = tk.IntVar()
        check_error = tk.Checkbutton(
            frame6,
            text="Show Error",
            highlightthickness=0,
            variable=self.show_error,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=SUNKEN,
        )
        check_error.grid(row=22, column=0, columnspan=3, padx=5, pady=5, sticky=E + W)
        self.show_error.set(0)

        """Frame7:  Plot Options"""

        def clearMax():
            if self.PlotMax_set.get() == 0:
                self.max_hold = -1000
                self.min_hold = 1000

        self.PlotMax_set = tk.IntVar()
        check_PlotMax = tk.Checkbutton(
            frame7,
            text="Show Peak Gain",
            highlightthickness=0,
            variable=self.PlotMax_set,
            command=clearMax,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=SUNKEN,
        )
        check_PlotMax.grid(
            row=0, column=0, columnspan=3, padx=20, pady=10, sticky=E + W
        )
        self.AngleMax_set = tk.IntVar()
        check_AngleMax = tk.Checkbutton(
            frame7,
            text="Show Peak Angle",
            highlightthickness=0,
            variable=self.AngleMax_set,
            onvalue=1,
            offvalue=0,
            anchor=W,
            relief=SUNKEN,
        )
        check_AngleMax.grid(
            row=1, column=0, columnspan=3, padx=20, pady=10, sticky=E + W
        )
        # self.HPBW_set = tk.IntVar()
        # check_HPBW = tk.Checkbutton(frame7, text="Shade 3dB Area (HPBW)", highlightthickness=0, variable=self.HPBW_set, onvalue=1, offvalue=0, anchor=W, relief=SUNKEN)
        # check_HPBW.grid(row=2, column=0, columnspan=3, padx=20, pady=20, sticky=E+W)
        # self.show_sum = tk.IntVar()
        # check_sum = tk.Checkbutton(frame7, text="Show Sum", highlightthickness=0, variable=self.show_sum, onvalue=1, offvalue=0, anchor=W, relief=SUNKEN)
        # check_sum.grid(row=0, column=3, columnspan=1, padx=20, pady=20, sticky=E+W)
        # self.show_sum.set(1)
        self.x_min = tk.DoubleVar()
        self.x_max = tk.DoubleVar()
        self.y_min = tk.DoubleVar()
        self.y_max = tk.DoubleVar()

        def check_axis(var_axis):
            x_minval = slide_x_min.get()
            x_maxval = slide_x_max.get()
            y_minval = slide_y_min.get()
            y_maxval = slide_y_max.get()
            if (x_minval) >= x_maxval:
                slide_x_min.set(x_maxval - 1)
            if y_minval >= y_maxval:
                slide_y_min.set(y_maxval - 1)

        slide_x_min = Scale(
            frame7,
            from_=-100,
            to=99,
            variable=self.x_min,
            command=check_axis,
            resolution=1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_x_min.grid(row=3, column=0, padx=10, pady=10, rowspan=3, columnspan=3)
        slide_x_min.set(-89)
        tk.Label(frame7, text="X axis min", relief=SUNKEN, anchor=W).grid(
            row=4, column=3, sticky=E + W
        )
        slide_x_max = Scale(
            frame7,
            from_=-99,
            to=100,
            variable=self.x_max,
            command=check_axis,
            resolution=1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_x_max.grid(row=6, column=0, padx=10, pady=10, rowspan=3, columnspan=3)
        slide_x_max.set(89)
        tk.Label(frame7, text="X axis max", relief=SUNKEN, anchor=W).grid(
            row=7, column=3, sticky=E + W
        )
        slide_y_min = Scale(
            frame7,
            from_=-100,
            to=9,
            variable=self.y_min,
            command=check_axis,
            resolution=1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_y_min.grid(row=9, column=0, padx=10, pady=10, rowspan=3, columnspan=3)
        slide_y_min.set(-50)
        tk.Label(frame7, text="Y axis min", relief=SUNKEN, anchor=W).grid(
            row=10, column=3, sticky=E + W
        )
        slide_y_max = Scale(
            frame7,
            from_=-59,
            to=10,
            variable=self.y_max,
            command=check_axis,
            resolution=1,
            troughcolor="LightYellow3",
            bd=2,
            orient=HORIZONTAL,
            relief=SUNKEN,
            length=200,
        )
        slide_y_max.grid(row=12, column=0, padx=10, pady=10, rowspan=3, columnspan=3)
        slide_y_max.set(0)
        tk.Label(frame7, text="Y axis max", relief=SUNKEN, anchor=W).grid(
            row=13, column=3, sticky=E + W
        )
        tk.Label(
            frame7,
            text="These options take effect with the next plot refresh",
            relief=SUNKEN,
            anchor=W,
        ).grid(row=20, column=0, columnspan=4, padx=20, pady=20, sticky=E + W)

        """CONFIGURE THE TABS FOR PLOTTING"""
        self.plot_tabs = ttk.Notebook(self.master)
        self.plot_tabs.grid(padx=10, pady=10, row=0, column=4, columnspan=5)
        self.plot_tabs.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.plot_tabs.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame11 = Frame(self.plot_tabs, width=700, height=500)
        self.frame11.grid(row=0, column=2)
        self.frame11.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame11.rowconfigure((0), weight=1)
        self.plot_tabs.add(self.frame11, text="Rectangular Plot")
        self.frame12 = Frame(self.plot_tabs, width=700, height=500)
        self.frame12.grid(row=0, column=2)
        self.frame12.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame12.rowconfigure((0), weight=1)
        self.plot_tabs.add(self.frame12, text="Polar Plot")
        self.frame13 = Frame(self.plot_tabs, width=700, height=500)
        self.frame13.grid(row=0, column=2)
        self.frame13.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame13.rowconfigure((0), weight=1)
        self.plot_tabs.add(self.frame13, text="FFT")
        self.frame14 = Frame(self.plot_tabs, width=700, height=500)
        self.frame14.grid(row=0, column=2)
        self.frame14.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame14.rowconfigure((0), weight=1)
        self.plot_tabs.add(self.frame14, text="Signal Tracking")
        self.plot_tabs.select(0)
        self.frame15 = Frame(self.plot_tabs, width=700, height=500)
        self.frame15.grid(row=0, column=2)
        self.frame15.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame15.rowconfigure((0), weight=1)
        self.plot_tabs.add(self.frame15, text="Signal vs Time")
        self.plot_tabs.select(0)

        def conf(event):
            self.plot_tabs.config(
                height=max(root.winfo_height() - 100, 500),
                width=max(root.winfo_width() - 450, 300),
            )

        def on_tab_change(event):
            if (
                self.plot_tabs.index(self.plot_tabs.select()) < 2
            ):  # so either rect plot of polar plot
                try:
                    self.plotData(1, 1, 0)
                except:
                    x = 0
            if self.plot_tabs.index(self.plot_tabs.select()) == 2:  # fft plot tab
                self.plotData(0, 1, 0)

        self.plot_tabs.bind("<<NotebookTabChanged>>", on_tab_change)

        root.bind("<Configure>", conf)
        self.generate_Figures()

        """ Add Lab Selection box """

        def Lab_mode_select(value):
            """ Reset all GUI values to default """
            print("Resetting all GUI values...")
            cntrl_tabs.select(frame1)  # Config tab
            self.plot_tabs.select(self.frame11)  # select rectangular plot
            cntrl_tabs.add(frame2)  # Gain tab
            cntrl_tabs.add(frame3)  # Phase tab
            cntrl_tabs.add(frame4)  # BW tab
            cntrl_tabs.add(frame5)  # Bits tab
            cntrl_tabs.add(frame6)  # Digital tab
            self.plot_tabs.add(self.frame14)  # Signal Tracking Plot
            self.plot_tabs.hide(self.frame15)  # Signal vs Time Plot
            mode_Menu.configure(state="normal")
            self.update_time.set(config.refresh_time)
            self.refresh.set(0)
            self.Tx_select.set("Transmit Disabled")
            Tx_mode_select("Transmit Disabled")
            slide_SignalFreq.set(config.SignalFreq / 1e9)
            slide_RxGain.set(int(config.Rx_gain))
            slide_RxPhaseDelta.set(0)
            self.mode_var.set("Beam Sweep")
            mode_select("Beam Sweep")
            self.Sym_set.set(0)
            taper_profile(1)  # set all gains to max (100)
            slide_Rx1Phase.set(0)
            slide_Rx2Phase.set(0)
            slide_Rx3Phase.set(0)
            slide_Rx4Phase.set(0)
            slide_Rx5Phase.set(0)
            slide_Rx6Phase.set(0)
            slide_Rx7Phase.set(0)
            slide_Rx8Phase.set(0)
            slide_SignalBW.set(self.SignalFreq / 1e9)
            slide_res.set(2.8125)
            slide_bits.set(7)
            self.res_bits.set(1)
            slide_B0_Phase.set(0)
            slide_B1_Phase.set(0)
            slide_B0_Gain.set(1)
            slide_B1_Gain.set(1)
            self.show_delta.set(0)
            self.show_error.set(0)
            self.PlotMax_set.set(0)
            self.AngleMax_set.set(0)
            if value == "Lab 1: Steering Angle":
                print(value)
                self.plot_tabs.select(self.frame13)  # select FFT plot
                cntrl_tabs.hide(frame2)  # Gain tab
                cntrl_tabs.hide(frame3)  # Phase tab
                cntrl_tabs.hide(frame4)  # BW tab
                cntrl_tabs.hide(frame5)  # Bits tab
                cntrl_tabs.hide(frame6)  # Digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Static Phase")
                mode_select("Static Phase")
                mode_Menu.configure(state="disabled")
                self.PlotMax_set.set(1)
                self.AngleMax_set.set(1)
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 2: Array Factor":
                print(value)
                self.plot_tabs.select(self.frame11)  # select rect plot
                # cntrl_tabs.hide(frame2)  # Gain tab
                cntrl_tabs.hide(frame3)  # Phase tab
                cntrl_tabs.hide(frame4)  # BW tab
                cntrl_tabs.hide(frame5)  # Bits tab
                cntrl_tabs.hide(frame6)  # Digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Beam Sweep")
                mode_select("Beam Sweep")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 3: Tapering" or value == "Lab 4: Grating Lobes":
                print(value)
                self.plot_tabs.select(self.frame11)  # select rect plot
                cntrl_tabs.select(frame2)  # select gain tab
                cntrl_tabs.hide(frame3)  # Phase tab
                cntrl_tabs.hide(frame4)  # BW tab
                cntrl_tabs.hide(frame5)  # Bits tab
                cntrl_tabs.hide(frame6)  # Digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Beam Sweep")
                mode_select("Beam Sweep")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 5: Beam Squint":
                print(value)
                self.plot_tabs.select(self.frame11)  # select rect plot
                cntrl_tabs.select(frame4)  # select BW tab
                cntrl_tabs.hide(frame3)  # Phase tab
                cntrl_tabs.hide(frame5)  # Bits tab
                cntrl_tabs.hide(frame6)  # Digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Beam Sweep")
                mode_select("Beam Sweep")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 6: Quantization":
                print(value)
                slide_res.set(1)
                slide_bits.set(7)
                self.res_bits.set(0)
                taper_profile(5)  # set blackman taper on the elements
                self.plot_tabs.add(self.frame15)  # Signal Tracking Plot
                self.plot_tabs.select(self.frame15)
                cntrl_tabs.select(frame1)  # select Config tab
                cntrl_tabs.hide(frame3)  # Phase tab
                cntrl_tabs.hide(frame6)  # Digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Signal vs Time")
                mode_select("Signal vs Time")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 7: Hybrid Control":
                print(value)
                self.plot_tabs.select(self.frame11)  # select rect plot
                cntrl_tabs.select(frame6)  # select digital tab
                self.plot_tabs.hide(self.frame14)  # Signal Tracking Plot
                self.mode_var.set("Beam Sweep")
                mode_select("Beam Sweep")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            elif value == "Lab 8: Monopulse Tracking":
                print(value)
                taper_profile(5)  # set blackman taper on the elements
                self.plot_tabs.select(self.frame11)  # select rect plot
                self.mode_var.set("Beam Sweep")
                mode_select("Beam Sweep")
                mode_Menu.configure(state="normal")
                self.refresh.set(1)
                self.updater()
            else:
                print("Enable All GUI Controls")

        self.Lab_select = StringVar()
        Lab_sel_menu = OptionMenu(
            self.master,
            self.Lab_select,
            "Lab 1: Steering Angle",
            "Lab 2: Array Factor",
            "Lab 3: Tapering",
            "Lab 4: Grating Lobes",
            "Lab 5: Beam Squint",
            "Lab 6: Quantization",
            "Lab 7: Hybrid Control",
            "Lab 8: Monopulse Tracking",
            "Enable All",
            command=Lab_mode_select,
        )
        Lab_sel_menu.grid(
            row=13, column=4, padx=20, pady=2, rowspan=13, columnspan=1, sticky=E + W
        )
        self.Lab_select.set(config.start_lab)
        Lab_mode_select(config.start_lab)

        """START THE UPDATER"""
        self.updater()

    def updater(self):
        # time1=datetime.datetime.now()
        self.programBeam()
        # time2=datetime.datetime.now()
        # time3=datetime.datetime.now()
        self.plotData(1, 1, 0)  # plot_gain, plot_fft, plot_tracking
        # time4=datetime.datetime.now()

        # for some reason, my Rpi4/2GB doesn't want to refersh the plot display over VNC.  So just do something quick to force it to update.
        do_something_to_refresh_gui = self.refresh.get()
        self.refresh.set(1)
        self.refresh.set(0)
        self.refresh.set(do_something_to_refresh_gui)

        self.refresh_time = self.update_time.get()
        if self.refresh.get() == 1:
            self.master.after(int(self.refresh_time / 1000), self.updater)

        # time5=datetime.datetime.now()
        # print("phase_update=", time2-time1,"    plot_update=", time4-time3)
        # print("total time=", time5-self.time0)
        # self.time0=datetime.datetime.now()

    def find_peak(self):
        self.programBeam()
        print("Begin Tracking Mode.  This will last about 20 seconds.")
        print(
            "Initial Steering Angle = ",
            int(self.ConvertPhaseToSteerAngle(self.max_PhDelta)),
            " deg",
        )
        i = 0
        # start=time.time()
        if (
            self.mode_var.get() == "Tracking"
        ):  # I realize this gets caught in a loop that you can't use the GUI during.  But I'm not having success with threading and TKinter....  Any ideas are welcome!
            # track_thread= Thread(target=self.track, args=(self.max_PhDelta,))
            # track_thread.start()
            # plot_thread = Thread(self.plotData, args=(0,0,1,))
            # plot_thread.start()
            # track_thread.join()
            for i in range(0, 1500):
                self.track(self.max_PhDelta)
                if i % 20 == 0:
                    self.plotData(0, 0, 1)
            self.mode_var.set("Beam Sweep")
        print(
            "End of Tracking Operation. To do tracking again, select the Tracking mode from the pulldown menu."
        )

    def track(self, PhDelta):
        phaseList = [
            self.RxPhase1,
            self.RxPhase2,
            self.RxPhase3,
            self.RxPhase4,
            self.RxPhase5,
            self.RxPhase6,
            self.RxPhase7,
            self.RxPhase8,
        ]
        ADAR_set_Phase(self.array, self.max_PhDelta, 2.8125, phaseList)
        (
            PeakValue_sum,
            PeakValue_delta,
            PeakValue_beam_phase,
            sum_chan,
            target_error,
        ) = self.getData(1)
        error_thresh = 0
        if target_error > (-1 * error_thresh):
            PhDelta = (
                PhDelta - 2.8125
            )  # depending on the orientation of Phaser to the source, this might need to be -2.8125
        elif target_error < (-1 * error_thresh):
            PhDelta = (
                PhDelta + 2.8125
            )  # depending on the orientation of Phaser to the source, this might need to be +2.8125
        SteerAngle = self.ConvertPhaseToSteerAngle(PhDelta)
        self.TrackArray.append(SteerAngle)
        self.max_PhDelta = PhDelta

    def closeProgram(self):
        self.refresh.set(0)
        time.sleep(0.5)
        """power down the Phaser board"""
        # this drops Pdiss from about 8.5W to 3.5W
        gpios.gpio_vctrl_1 = 0  # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
        gpios.gpio_vctrl_2 = 0  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
        for device in self.array.devices.values():
            device.reset()  # resets the ADAR1000s
        SDR_TxBuffer_Destroy(self.sdr)
        # self.master.destroy()
        sys.exit(0)

    def programTaper(self):
        g1 = self.Rx1Gain_set.get()
        g2 = self.Rx2Gain_set.get()
        g3 = self.Rx3Gain_set.get()
        g4 = self.Rx4Gain_set.get()
        g5 = self.Rx5Gain_set.get()
        g6 = self.Rx6Gain_set.get()
        g7 = self.Rx7Gain_set.get()
        g8 = self.Rx8Gain_set.get()
        # MWT: use np.array_equal function to detect any differences.
        if (
            self.RxGain1 != g1
            or self.RxGain2 != g2
            or self.RxGain3 != g3
            or self.RxGain4 != g4
            or self.RxGain5 != g5
            or self.RxGain6 != g6
            or self.RxGain7 != g7
            or self.RxGain8 != g8
        ):
            self.RxGain1 = g1
            self.RxGain2 = g2
            self.RxGain3 = g3
            self.RxGain4 = g4
            self.RxGain5 = g5
            self.RxGain6 = g6
            self.RxGain7 = g7
            self.RxGain8 = g8
            gainList = [
                self.RxGain1,
                self.RxGain2,
                self.RxGain3,
                self.RxGain4,
                self.RxGain5,
                self.RxGain6,
                self.RxGain7,
                self.RxGain8,
            ]
            ADAR_set_Taper(self.array, gainList)

    def programLO(self):
        if self.SignalFreq != int(self.freq.get() * 1e9):
            self.SignalFreq = self.freq.get() * 1e9
            self.LO_freq = self.SignalFreq + self.Rx_freq
            SDR_LO_init(rpi_ip, self.LO_freq)
        if self.Rx_gain != int(self.RxGain.get()):
            self.Rx_gain = int(self.RxGain.get())
            SDR_setRx(self.sdr, self.Rx_gain, self.Rx_gain)
        if self.Tx_gain != int(self.TxGain.get()):
            self.Tx_gain = int(self.TxGain.get())
            SDR_setTx(self.sdr, self.Tx_gain)

    def ConvertPhaseToSteerAngle(self, PhDelta):
        # steering angle theta = arcsin(c*deltaphase/(2*pi*f*d)
        value1 = (self.c * np.radians(np.abs(PhDelta))) / (
            2 * 3.14159 * (self.SignalFreq - self.bandwidth * 1000000) * self.d
        )
        clamped_value1 = max(
            min(1, value1), -1
        )  # arcsin argument must be between 1 and -1, or numpy will throw a warning
        theta = np.degrees(np.arcsin(clamped_value1))
        if PhDelta >= 0:
            SteerAngle = theta  # positive PhaseDelta covers 0deg to 90 deg
        else:
            SteerAngle = -theta  # negative phase delta covers 0 deg to -90 deg
        return SteerAngle

    def getData(self, Averages):
        total_sum = 0
        total_delta = 0
        total_beam_phase = 0
        for count in range(0, Averages):
            data = SDR_getData(self.sdr)
            chan1 = data[0]  # Rx1 data
            chan2 = data[1]  # Rx2 data

            # scale the amplitude from the "digital tab"
            chan1 = chan1 * self.B0_Gain_set.get()
            chan2 = chan2 * self.B1_Gain_set.get()

            # shift phase from the "digital tab"
            NumSamples = len(chan1)
            dig_Beam0_phase = np.deg2rad(self.Beam0_Phase_set.get())
            dig_Beam1_phase = np.deg2rad(self.Beam1_Phase_set.get())
            if dig_Beam0_phase != 0:
                chan1_fft_shift = np.fft.fft(chan1) * np.exp(1.0j * dig_Beam0_phase)
                chan1 = np.fft.ifft(chan1_fft_shift, n=NumSamples)
                chan1 = chan1[0:NumSamples]
            if dig_Beam1_phase != 0:
                chan2_fft_shift = np.fft.fft(chan2) * np.exp(1.0j * dig_Beam1_phase)
                chan2 = np.fft.ifft(chan2_fft_shift, n=NumSamples)
                chan2 = chan2[0:NumSamples]

            sum_chan = chan1 + chan2
            delta_chan = chan1 - chan2
            # for the electrical scan, the right way to do this is to take an FFT the get the peak of it
            # but, for our purposes, keeping it in the time domain and looking at peak and angles there is faster
            # this works the same as freq domain, as long as there is one strong signal (i.e. not multiple peaks)
            max_index = np.argmax(sum_chan)
            s_mag_sum = np.max(
                [np.abs(sum_chan[max_index]), 10 ** (-15)]
            )  # make sure this gives something >0, otherwise the log10 function will give an error
            s_mag_delta = np.max([np.abs(delta_chan[max_index]), 10 ** (-15)])
            s_dbfs_sum = 20 * np.log10(s_mag_sum / (2 ** 11))
            s_dbfs_delta = 20 * np.log10(s_mag_delta / (2 ** 11))
            total_beam_phase = total_beam_phase + (
                np.angle(sum_chan[max_index]) - np.angle(delta_chan[max_index])
            )
            total_sum = total_sum + (
                s_dbfs_sum
            )  # sum up all the loops, then we'll average
            total_delta = total_delta + (
                s_dbfs_delta
            )  # sum up all the loops, then we'll average

        PeakValue_sum = total_sum / Averages
        PeakValue_delta = total_delta / Averages
        PeakValue_beam_phase = total_beam_phase / Averages
        if np.sign(PeakValue_beam_phase) == -1:
            target_error = min(
                -0.01,
                (
                    np.sign(PeakValue_beam_phase) * (PeakValue_sum - PeakValue_delta)
                    + np.sign(PeakValue_beam_phase)
                    * (PeakValue_sum + PeakValue_delta)
                    / 2
                )
                / (PeakValue_sum + PeakValue_delta),
            )
        else:
            target_error = max(
                0.01,
                (
                    np.sign(PeakValue_beam_phase) * (PeakValue_sum - PeakValue_delta)
                    + np.sign(PeakValue_beam_phase)
                    * (PeakValue_sum + PeakValue_delta)
                    / 2
                )
                / (PeakValue_sum + PeakValue_delta),
            )
        return (
            PeakValue_sum,
            PeakValue_delta,
            PeakValue_beam_phase,
            sum_chan,
            target_error,
        )

    def programBeam(self):
        self.programLO()
        self.programTaper()
        steer_res = max(self.res.get(), 0.1)
        phase_step_size = 360 / (2 ** self.bits.get())
        self.bandwidth = self.BW.get()
        self.RxSignal_text.set(
            str("Signal Bandwidth = " + str(self.bandwidth) + " MHz")
        )
        self.MixerLO_text.set(
            str("LTC5548 LO Freq = " + str(int(self.LO_freq / 1000000)) + " MHz")
        )
        self.PlutoRxLO_text.set(
            str("Pluto Rx LO = " + str(int(self.Rx_freq / 1000000)) + " MHz")
        )
        self.BeamCalc_text.set(
            str(
                "Beam Calculated at "
                + str(int(self.SignalFreq / 1000000 - self.bandwidth))
                + " MHz"
            )
        )
        self.AngleMeas_text.set(
            str("Beam Measured at " + str(int(self.SignalFreq / 1000000)) + " MHz")
        )

        SteerValues = np.arange(
            -90, 90 + steer_res, steer_res
        )  # convert degrees to radians
        # Phase delta = 2*Pi*d*sin(theta)/lambda = 2*Pi*d*sin(theta)*f/c
        PhaseValues = np.degrees(
            2
            * 3.14159
            * self.d
            * np.sin(np.radians(SteerValues))
            * self.SignalFreq
            / self.c
        )
        self.res_text.set(str("Phase Shift LSB = " + str(phase_step_size)) + " deg")
        if self.res_bits.get() == 1:
            phase_limit = int(225 / phase_step_size) * phase_step_size + phase_step_size
            PhaseValues = np.arange(-phase_limit, phase_limit, phase_step_size)
        if (
            self.mode_var.get() == "Static Phase"
            or self.mode_var.get() == "Signal vs Time"
        ):
            PhaseValues = np.degrees(
                2
                * 3.14159
                * self.d
                * np.sin(np.radians([self.RxPhaseDelta.get()]))
                * self.SignalFreq
                / self.c
            )
            step_size = phase_step_size  # 2.8125
            if int(self.RxPhaseDelta.get()) < 0:
                e1 = 360
            else:
                e1 = 0
            e2 = ((np.rint(PhaseValues[0] * 1 / step_size) * step_size)) % 360
            e3 = ((np.rint(PhaseValues[0] * 2 / step_size) * step_size)) % 360
            e4 = ((np.rint(PhaseValues[0] * 3 / step_size) * step_size)) % 360
            e5 = ((np.rint(PhaseValues[0] * 4 / step_size) * step_size)) % 360
            e6 = ((np.rint(PhaseValues[0] * 5 / step_size) * step_size)) % 360
            e7 = ((np.rint(PhaseValues[0] * 6 / step_size) * step_size)) % 360
            e8 = ((np.rint(PhaseValues[0] * 7 / step_size) * step_size)) % 360
            self.PhaseVal_text.set(
                str(int(e1))
                + ", "
                + str(int(e2))
                + ", "
                + str(int(e3))
                + ", "
                + str(int(e4))
                + ", "
                + str(int(e5))
                + ", "
                + str(int(e6))
                + ", "
                + str(int(e7))
                + ", "
                + str(int(e8))
            )
        """if self.mode_var.get() == "Signal vs Time":
            PhaseValues = np.degrees(
                2 * 3.14159 * self.d
                * np.sin(np.radians([self.RxPhaseDelta.get()]))
                * self.SignalFreq / self.c )"""
        gain = []
        delta = []
        beam_phase = []
        angle = []
        diff_error = []
        self.max_gain = []
        max_signal = -100000
        max_angle = -90
        self.RxPhase1 = self.Rx1Phase_set.get() + self.Rx1_cal
        self.RxPhase2 = self.Rx2Phase_set.get() + self.Rx2_cal
        self.RxPhase3 = self.Rx3Phase_set.get() + self.Rx3_cal
        self.RxPhase4 = self.Rx4Phase_set.get() + self.Rx4_cal
        self.RxPhase5 = self.Rx5Phase_set.get() + self.Rx5_cal
        self.RxPhase6 = self.Rx6Phase_set.get() + self.Rx6_cal
        self.RxPhase7 = self.Rx7Phase_set.get() + self.Rx7_cal
        self.RxPhase8 = self.Rx8Phase_set.get() + self.Rx8_cal

        phaseList = [
            self.RxPhase1,
            self.RxPhase2,
            self.RxPhase3,
            self.RxPhase4,
            self.RxPhase5,
            self.RxPhase6,
            self.RxPhase7,
            self.RxPhase8,
        ]
        for PhDelta in PhaseValues:
            # if self.refresh.get()==1:
            # time.sleep((self.update_time.get()/1000)/100)
            ADAR_set_Phase(self.array, PhDelta, phase_step_size, phaseList)
            # self.array.devices[1].generate_clocks()
            # gpios.gpio_rx_load = 1  # RX_LOAD for ADAR1000 RAM access
            # gpios.gpio_rx_load = 0  # RX_LOAD for ADAR1000 RAM access
            SteerAngle = self.ConvertPhaseToSteerAngle(PhDelta)
            (
                PeakValue_sum,
                PeakValue_delta,
                PeakValue_beam_phase,
                sum_chan,
                target_error,
            ) = self.getData(self.Averages)

            if (
                PeakValue_sum > max_signal
            ):  # for the largest value, save the data so we can plot it in the FFT window
                max_signal = PeakValue_sum
                max_angle = PeakValue_beam_phase
                self.max_PhDelta = PhDelta
                data_fft = sum_chan
            if self.mode_var.get() != "Signal vs Time":
                gain.append(PeakValue_sum)
                delta.append(PeakValue_delta)
                beam_phase.append(PeakValue_beam_phase)
                angle.append(SteerAngle)
                diff_error.append(target_error)

            if self.mode_var.get() == "Signal vs Time":
                time.sleep(0.1)
                self.Gain_time.append(PeakValue_sum)
                self.Gain_time = self.Gain_time[-100:]

        # take the FFT of the raw data ("data_fft") which corresponded to the peak gain
        NumSamples = len(data_fft)  # number of samples
        win = np.blackman(NumSamples)
        y = data_fft * win
        sp = np.absolute(np.fft.fft(y))
        sp = np.fft.fftshift(sp)
        s_mag = np.abs(sp) / np.sum(
            win
        )  # Scale FFT by window and /2 since we are using half the FFT spectrum
        s_mag = np.maximum(s_mag, 10 ** (-15))
        self.max_gain = 20 * np.log10(
            s_mag / (2 ** 11)
        )  # Pluto is a 12 bit ADC, but we're only looking at positive #'s, so use 2**11
        ts = 1 / float(self.SampleRate)
        self.xf = np.fft.fftfreq(NumSamples, ts)
        self.xf = np.fft.fftshift(
            self.xf
        )  # this is the x axis (freq in Hz) for our fft plot

        if self.mode_var.get() != "Signal vs Time":
            self.ArrayGain = gain
            self.ArrayDelta = delta
            self.ArrayBeamPhase = beam_phase
            self.ArrayAngle = angle
            self.ArrayError = diff_error
            self.peak_gain = max(self.ArrayGain)
            index_peak_gain = np.where(self.ArrayGain == self.peak_gain)
            index_peak_gain = index_peak_gain[0]
            self.max_angle = self.ArrayAngle[int(index_peak_gain[0])]

    def generate_Figures(self):
        plt.clf()
        self.figure1 = plt.Figure(figsize=(4, 3), dpi=100)
        self.ax2 = self.figure1.add_subplot(3, 1, 3)  # this plot is in the 3rd cell

        self.ax1 = self.figure1.add_subplot(
            3, 1, (1, 2)
        )  # this plot is in the first and second cell, so has 2x the height
        self.ax1.set_title("Array Signal Strength vs Steering Angle")
        # self.ax1.set_xlabel('Steering Angle (deg)')
        self.ax1.set_ylabel("Amplitude (dBFS)")
        x_axis_min = self.x_min.get()
        x_axis_max = self.x_max.get()
        y_axis_min = self.y_min.get()
        y_axis_max = self.y_max.get()
        self.ax1.set_xlim([x_axis_min, x_axis_max])
        self.ax1.set_ylim([y_axis_min, y_axis_max])
        self.sum_line = self.ax1.plot(
            self.ArrayAngle,
            self.ArrayGain,
            "-o",
            ms=3,
            alpha=0.7,
            mfc="blue",
            color="blue",
        )
        self.delta_line = self.ax1.plot(
            self.ArrayAngle,
            self.ArrayGain,
            "-o",
            ms=3,
            alpha=0.7,
            mfc="red",
            color="red",
        )
        self.saved_line = self.ax1.plot(
            self.saved_angle,
            self.saved_gain,
            "-o",
            ms=1,
            alpha=0.5,
            mfc="green",
            color="green",
        )
        self.saved_lineB = self.ax1.plot(
            self.saved_angleB,
            self.saved_gainB,
            "-o",
            ms=1,
            alpha=0.5,
            mfc="purple",
            color="purple",
        )
        self.ax1.legend(["Sum", "Delta"], loc="lower right")
        self.max_gain_line = self.ax1.plot(
            self.ArrayAngle,
            np.full(len(self.ArrayAngle), 0),
            color="blue",
            linestyle="--",
            alpha=0.3,
        )
        self.max_angle_line = self.ax1.plot(
            self.ArrayAngle,
            np.full(len(self.ArrayAngle), 0),
            color="red",
            linestyle=":",
            alpha=0.3,
        )

        self.ax1.grid(True)

        self.phase_line = self.ax2.plot(
            self.ArrayAngle,
            np.sign(self.ArrayBeamPhase),
            "-o",
            ms=3,
            alpha=0.7,
            mfc="blue",
            color="blue",
        )
        self.error_line = self.ax2.plot(
            self.ArrayAngle,
            self.ArrayError,
            "-o",
            ms=3,
            alpha=0.7,
            mfc="red",
            color="red",
        )
        self.ax2.legend(["Phase Difference", "Error Function"], loc="upper right")
        self.ax2.set_xlabel("Steering Angle (deg)")
        self.ax2.set_ylabel("Error Function")
        self.ax2.set_xlim([x_axis_min, x_axis_max])
        self.ax2.set_ylim([-1.5, 1.5])
        self.ax2.grid(True)

        self.graph1 = FigureCanvasTkAgg(self.figure1, self.frame11)
        self.graph1.draw()
        self.graph1.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        plt.show(block=False)
        plt.pause(0.01)
        plt.close()

        self.ax1.add_line(self.sum_line[0])
        self.ax1.add_line(self.saved_line[0])
        self.ax1.add_line(self.saved_lineB[0])
        self.ax1.add_line(self.delta_line[0])
        self.ax1.add_line(self.max_gain_line[0])
        self.ax1.add_line(self.max_angle_line[0])
        self.ax2.add_line(self.phase_line[0])
        self.ax2.add_line(self.error_line[0])

        self.toolbar1 = NavigationToolbar2Tk(self.graph1, self.frame11)
        self.toolbar1.update()

        self.polar1 = plt.Figure(figsize=(1, 1), dpi=100)
        self.pol_ax1 = self.polar1.add_subplot(111, projection="polar")
        self.pol_graph1 = FigureCanvasTkAgg(self.polar1, self.frame12)
        self.polar1.subplots_adjust(0, 0, 1, 1)
        self.pol_graph1.draw()
        self.pol_graph1.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.toolbar2 = NavigationToolbar2Tk(self.pol_graph1, self.frame12)
        self.toolbar2.update()

        self.figure3 = plt.Figure(figsize=(4, 3), dpi=100)
        self.ax3 = self.figure3.add_subplot(111)
        self.graph3 = FigureCanvasTkAgg(self.figure3, self.frame13)
        self.graph3.draw()
        self.graph3.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.toolbar3 = NavigationToolbar2Tk(self.graph3, self.frame13)
        self.toolbar3.update()

        self.figure4 = plt.Figure(figsize=(4, 3), dpi=100)
        self.ax4 = self.figure4.add_subplot(111)
        self.graph4 = FigureCanvasTkAgg(self.figure4, self.frame14)
        self.graph4.draw()
        self.graph4.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.toolbar4 = NavigationToolbar2Tk(self.graph4, self.frame14)
        self.toolbar4.update()

        self.figure5 = plt.Figure(figsize=(4, 3), dpi=100)
        self.ax5 = self.figure5.add_subplot(111)
        self.graph5 = FigureCanvasTkAgg(self.figure5, self.frame15)
        self.graph5.draw()
        self.graph5.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.toolbar5 = NavigationToolbar2Tk(self.graph5, self.frame15)
        self.toolbar5.update()

        self.background1 = self.graph1.copy_from_bbox(self.ax1.bbox)
        self.background2 = self.graph1.copy_from_bbox(self.ax2.bbox)

    def savePlot(self):
        self.saved_gain = self.ArrayGain
        self.saved_angle = self.ArrayAngle
        np.savetxt(
            "saved_plot_A.txt",
            (self.saved_angle, self.saved_gain),
            delimiter=",",
            header="steering angle array (first), then FFT amplitude array",
        )
        print("data saved to saved_plot_A.txt")

    def savePlotB(self):
        self.saved_gainB = self.ArrayGain
        self.saved_angleB = self.ArrayAngle
        np.savetxt(
            "saved_plot_B.txt",
            (self.saved_angleB, self.saved_gainB),
            delimiter=",",
            header="steering angle array (first), then FFT amplitude array",
        )
        print("data saved to saved_plot_B.txt")

    def clearPlot(self):
        self.saved_gain = []
        self.saved_angle = []
        self.saved_gainB = []
        self.saved_angleB = []

    def plotData(self, plot_gain, plot_fft, plot_tracking):
        # plot sum of both channels and subtraction of both channels
        x_axis_min = self.x_min.get()
        x_axis_max = self.x_max.get()
        y_axis_min = self.y_min.get()
        y_axis_max = self.y_max.get()
        self.ax1.set_xlim([x_axis_min, x_axis_max])
        self.ax1.set_ylim([y_axis_min, y_axis_max])

        if self.mode_var.get() == "Signal vs Time":
            # time.sleep(0.1)
            self.ArrayGain = self.Gain_time
            self.ArrayAngle = []
            num_gains = len(self.ArrayGain)
            for i in range(num_gains):
                self.ArrayAngle.append(180 / num_gains * i - 90)
        else:
            self.saved_line[0].set_data(self.saved_angle, self.saved_gain)
            self.saved_lineB[0].set_data(self.saved_angleB, self.saved_gainB)
            if self.show_delta.get() == 1:
                self.delta_line[0].set_data(self.ArrayAngle, self.ArrayDelta)
            if self.PlotMax_set.get() == 1:
                self.max_gain_line[0].set_data(
                    [x_axis_min, x_axis_max], [self.peak_gain, self.peak_gain]
                )
            if self.AngleMax_set.get() == 1:
                self.max_angle_line[0].set_data(
                    [self.max_angle, self.max_angle], [y_axis_min, y_axis_max]
                )

        self.sum_line[0].set_data(self.ArrayAngle, self.ArrayGain)

        self.graph1.restore_region(self.background1)
        self.graph1.restore_region(self.background2)

        self.ax1.draw_artist(self.sum_line[0])
        if self.mode_var.get() != "Signal vs Time":
            self.ax1.draw_artist(self.saved_line[0])
            self.ax1.draw_artist(self.saved_lineB[0])
            if self.show_delta.get() == 1:
                self.ax1.draw_artist(self.delta_line[0])
            if self.PlotMax_set.get() == 1:
                self.ax1.draw_artist(self.max_gain_line[0])
            if self.AngleMax_set.get() == 1:
                self.ax1.draw_artist(self.max_angle_line[0])
            if self.show_error.get() == 1:
                self.ax2.set_xlim([x_axis_min, x_axis_max])
                self.ax2.set_ylim([-1.5, 1.5])
                self.phase_line[0].set_data(
                    self.ArrayAngle, np.sign(self.ArrayBeamPhase)
                )
                self.error_line[0].set_data(self.ArrayAngle, self.ArrayError)
                # self.graph1.restore_region(self.background2)
                self.ax2.draw_artist(self.phase_line[0])
                self.ax2.draw_artist(self.error_line[0])

        self.graph1.blit(self.ax1.bbox)
        self.graph1.blit(self.ax2.bbox)
        self.graph1.flush_events()

        # Polar Plot
        if plot_gain == 1 and self.plot_tabs.index(self.plot_tabs.select()) == 1:
            y_axis_min = self.y_min.get()
            y_axis_max = self.y_max.get()
            self.pol_ax1.cla()
            self.pol_ax1.plot(
                np.radians(self.ArrayAngle),
                self.ArrayGain,
                "-o",
                ms=3,
                alpha=0.7,
                mfc="blue",
                color="blue",
            )
            if self.mode_var.get() != "Signal vs Time":
                self.pol_ax1.plot(
                    np.radians(self.saved_angle),
                    self.saved_gain,
                    "-o",
                    ms=1,
                    alpha=0.5,
                    mfc="green",
                    color="green",
                )
                self.pol_ax1.plot(
                    np.radians(self.saved_angleB),
                    self.saved_gainB,
                    "-o",
                    ms=1,
                    alpha=0.5,
                    mfc="purple",
                    color="purple",
                )
            self.pol_ax1.set_theta_offset(
                np.pi / 2
            )  # rotate polar axis so that 0 deg is on top
            self.pol_ax1.set_theta_direction(-1)
            self.pol_ax1.set_thetamin(-89)
            self.pol_ax1.set_thetamax(89)
            self.pol_ax1.set_rmin(y_axis_min)
            self.pol_ax1.set_rmax(y_axis_max)
            self.pol_graph1.draw()

        # FFT Spectrum
        if plot_fft == 1 and self.plot_tabs.index(self.plot_tabs.select()) == 2:
            x_axis_min = self.x_min.get()
            x_axis_max = self.x_max.get()
            y_axis_min = self.y_min.get()
            y_axis_max = self.y_max.get()
            self.ax3.cla()
            self.ax3.plot(-self.xf / 1e6, self.max_gain)
            self.ax3.set_title("FFT at Peak Steering Angle")
            self.ax3.set_xlabel("Freq (MHz)")
            # self.ax3.set_xlabel(f"Freq - {int(self.SignalFreq/1e6)} MHz")
            self.ax3.set_ylabel("Amplitude (dBFS)")
            # self.ax3.set_xlim([x_axis_min, x_axis_max])
            self.ax3.set_ylim([-100, y_axis_max])
            self.ax3.grid()
            max_fft_gain = max(self.max_gain)
            index_max_fft_gain = np.where(self.max_gain == max_fft_gain)
            try:
                max_freq = (
                    self.xf[int(index_max_fft_gain[0])] / 1e6
                )  # if both digital gains are 0, then this barfs.
            except:
                max_freq = 0
            if self.PlotMax_set.get() == 1:
                self.max_hold = max(self.max_hold, max_fft_gain)
                self.min_hold = min(self.min_hold, max_fft_gain)
                self.ax3.axhline(
                    y=max_fft_gain, color="blue", linestyle="--", alpha=0.3
                )
                self.ax3.axhline(
                    y=self.max_hold, color="green", linestyle="--", alpha=0.3
                )
                self.ax3.axhline(
                    y=self.min_hold, color="red", linestyle="--", alpha=0.3
                )
            if self.AngleMax_set.get() == 1:
                self.ax3.axvline(x=max_freq, color="orange", linestyle=":", alpha=0.5)
            self.graph3.draw()

        # Monopulse Tracking Waterfall Plot
        if plot_tracking == 1:
            self.TrackArray = self.TrackArray[-1000:]  # just use the last elements
            self.ax4.cla()
            self.ax4.plot(
                self.TrackArray[-1000:],
                range(0, 10000, 10),
                "-o",
                ms=3,
                alpha=0.7,
                mfc="blue",
            )
            self.ax4.set_xlabel("Steering Angle (deg)")
            self.ax4.set_ylabel("time (ms)")
            self.ax4.set_xlim([-60, 60])
            # self.ax4.set_ylim([-1, 1])
            self.ax4.grid()
            self.graph4.draw()

        if self.mode_var.get() == "Signal vs Time":
            self.ax5.cla()
            self.ax5.plot(
                self.ArrayAngle,
                self.ArrayGain,
                "-o",
                ms=3,
                alpha=0.7,
                mfc="blue",
                color="blue",
            )
            self.ax5.set_xlabel("time")
            self.ax5.set_ylabel("Amplitude (dBFS)")
            self.ax5.set_xlim([-89, 89])
            self.ax5.set_ylim([-50, 0])
            self.ax5.set_xticklabels([])  # hide the x axis numbers
            self.ax5.grid()
            self.graph5.draw()


# Some notes on TKinter scaling issues:
# The root.tk.call('tk', 'scaling', 2.0) takes one argument, which is the number of pixels in one "point".
# A point is 1/72 of an inch, so a scaling factor of 1.0 is appropriate for a 72DPI display.
# https://coderslegacy.com/python/problem-solving/improve-tkinter-resolution/


# Another method that might help scaling issues... so far the scaling method seems to work better.
# import ctypes
# ctypes.windll.shcore.SetProcessDpiAwareness(1)

root = Tk()
root.title("Phased Array Beamforming")
root.geometry("1600x800+100+20")
root.call("tk", "scaling", 1.50)  # MWT: This seemed to fix scaling issues in Windows.
# Verify it doesn't mess anything up on the Pi, detect os if so.
root.resizable(
    False, False
)  # the GUI is setup to be resizeable--and it all works great.
# EXCEPT when we do the blitting of the graphs ( to speed up redraw time).  I can't figure that out.  So, for now, I just made it un-resizeable...
root.minsize(700, 600)
app = App(root)
root.mainloop()
