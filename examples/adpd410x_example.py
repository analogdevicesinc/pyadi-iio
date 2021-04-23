# File: adpd410x_example.py
# Description: IIO python script example for ADPD410x
# Author: Antoniu Miclaus (antoniu.miclaus@analog.com)
#
# Copyright 2021(c) Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  - Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  - Neither the name of Analog Devices, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#  - The use of this software may or may not infringe the patent rights
#    of one or more patent holders.  This license does not release you
#    from the requirement that you obtain separate licenses from these
#    patent holders to use this software.
#  - Use of the software either in source or binary form, must be run
#    on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT,
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, INTELLECTUAL PROPERTY RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import time

import adi

try:

    import tkinter as tk
    from tkinter import filedialog
    import tkinter.scrolledtext as tkscrolled

except:
    print("Please install tkinter")
try:
    import csv
except:
    print("Please install csv")
try:
    import pandas as pd
except:
    print("Please install pandas")
try:
    import numpy as np
except:
    print("Please install numpy")

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg,
        NavigationToolbar2Tk,
    )
except:
    print("Please install matplotlib")

# Setup device - get device data
def read_device():

    global adpd410x, raw

    raw = []

    for idx in range(8):
        raw.append(adpd410x.channel[idx].raw)

    txt1.delete("1.0", tk.END)
    txt1.insert(tk.END, "LED1A + LED2A:\n")
    txt1.insert(tk.END, "IN1: " + hex(raw[0]) + "\n")
    txt1.insert(tk.END, "IN2: " + hex(raw[1]) + "\n")
    txt1.insert(tk.END, "LED3A + LED4A:\n")
    txt1.insert(tk.END, "IN3: " + hex(raw[2]) + "\n")
    txt1.insert(tk.END, "IN4: " + hex(raw[3]) + "\n")
    txt1.insert(tk.END, "LED1B + LED2B:\n")
    txt1.insert(tk.END, "IN5: " + hex(raw[4]) + "\n")
    txt1.insert(tk.END, "IN6: " + hex(raw[5]) + "\n")
    txt1.insert(tk.END, "LED3B + LED4B:\n")
    txt1.insert(tk.END, "IN7: " + hex(raw[6]) + "\n")
    txt1.insert(tk.END, "IN8: " + hex(raw[7]) + "\n")


def connect_device():
    global adpd410x, btn_text

    if adpd410x is None:
        adpd410x = adi.adpd410x(uri="serial:" + comport.get() + ",115200")

    btn_text.set("Connected!!!")


# Create GUI
def gui():

    global dev, comport, adpd410x, btn_text, txt1
    global adpd410x

    adpd410x = None

    root = tk.Tk()
    root.title("ADPD410x (Analog Devices, Inc.)")

    btn_text = tk.StringVar()
    comport = tk.StringVar()

    btn_text.set("Connect")

    fr1 = tk.Frame(root)
    fr1.pack(side=tk.LEFT, anchor="n", padx=10, pady=10)

    fr2 = tk.Frame(fr1)
    fr2.grid(row=0, column=0, pady=10)

    fr3 = tk.Frame(fr1)
    fr3.grid(row=1, column=0)

    label1 = tk.Label(fr2, text="COMPort:")
    label1.grid(row=4, column=0)

    entry1 = tk.Entry(fr2, textvariable=comport)
    entry1.grid(row=4, column=1)

    txt1 = tkscrolled.ScrolledText(fr3, width=40, height=20)
    txt1.grid(row=1, column=0)
    txt1.config(fg="black")

    btn_sweep = tk.Button(fr2, text="Read", command=read_device)
    btn_sweep.config(width=13, height=1, bg="orange")
    btn_sweep.grid(row=8, column=0, pady=(10, 0))

    btn_connect = tk.Button(fr2, textvariable=btn_text, command=connect_device)
    btn_connect.config(width=13, height=1, bg="red")
    btn_connect.grid(row=8, column=1, pady=(10, 0))

    root.update_idletasks()

    root.mainloop()


# main function
def main():

    global adpd410x
    gui()

    del dev


main()
