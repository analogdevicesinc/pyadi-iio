# --------------------LICENSE AGREEMENT----------------------------------------
# Copyright (c) 2020 Analog Devices, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#   - Modified versions of the software must be conspicuously marked as such.
#   - This software is licensed solely and exclusively for use with
#   processors/products manufactured by or for Analog Devices, Inc.
#   - This software may not be combined or merged with other code in any manner
#   that would cause the software to become subject to terms and conditions
#   which differ from those listed here.
#   - Neither the name of Analog Devices, Inc. nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#   - The use of this software may or may not infringe the patent rights of
#   one or more patent holders.  This license does not release you from the
#   requirement that you obtain separate licenses from these patent holders
#   to use this software.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES, INC. AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# NON-INFRINGEMENT, TITLE, MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ANALOG DEVICES, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, PUNITIVE OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# DAMAGES ARISING OUT OF CLAIMS OF INTELLECTUAL PROPERTY RIGHTS INFRINGEMENT;
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# 2020-02-24-7CBSD SLA
# -----------------------------------------------------------------------------


import csv
import queue
import sys
import threading
import time

import adi
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sin_params as sp

# Other parameters to configure data
device_name = "ad4630-24"
fs = 2000000  # Sampling Frequency
N = 2 ** 10  # Length of rx buffer
get_data_for_secs = 6
data_collection = "log_data"  # you can either plot_data or log_data

# Plotting 4 different channels continuously requires 4 different threads. Here for example purpose only single channel
# is plotted at a time
signal_to_plot = (
    "differential0"  # options are differential0, differential1, common0, common1
)


class ad463x_plot:
    """ Ad4630 continuous sampling."""

    def __init__(self):
        """ Instantiate the device and set th parameters."""

        self.t1 = threading.Thread(
            target=self.start_sampling
        )  # Thread to sample data continuously
        self.t2 = threading.Thread(
            target=self.plot
        )  # Thread executed to plot data if data collection method is plot
        self.t3 = threading.Thread(
            target=self.log
        )  # Thread executed to log data if data collection method is log_data

        """ Enter device name from ad463x family and ip address of your host machine for e.g. ZEDboard
            to know the ip address of host PC go onto host via serial communication and type 'ifconfig -a' on terminal
            note ipv6 of usb0 and enter it in ip address. If you have ethernet connected you can use analog.local"""
        self.adc = adi.ad4630(uri="ip:analog.local", device_name=device_name)

        """ size of buffer it can be any where from 2 to 2**21 (For conti sampling it shouldn't matter)"""
        self.adc.rx_buffer_size = N
        self.adc.sample_rate = fs  # Sampling Rate of ADC

        """To switch the device b/w low_power_mode and normal_operating_mode."""
        self.adc.operating_mode = "normal_operating_mode"

        """ Prints Current output data mode"""
        print(self.adc.output_data_mode)

        """sample_averaging is only supported by 30bit mode. and in this mode it cannot be OFF."""
        if self.adc.output_data_mode == "30bit_avg":
            self.adc.sample_averaging = 64

        """ Differential Channel attributes"""
        if self.adc.output_data_mode != "32bit_test_pattern":
            self.adc.chan0.hw_gain = 1
            self.adc.chan0.offset = 0
            if device_name == "ad4630-24":
                self.adc.chan1.hw_gain = 1
                self.adc.chan1.offset = 0
        self.q = queue.Queue(maxsize=0)  # Queue to stuff sampled data
        self.data_getter()  # Function executing threads depending on data collection method

    def data_getter(self):
        """Function to start data collection thread and plot/log it accordingly"""

        self.t1.start()
        self.t_start = time.time()
        if data_collection == "plot_data":
            time.sleep(5)  # start plotting data after 5 Seconds
            self.t2.start()

        elif data_collection == "log_data":
            time.sleep(1)
            self.t3.start()

    def start_sampling(self):
        """Continuously Sample data and stuff it in a queue."""

        t_end = time.time() + get_data_for_secs
        while time.time() < t_end:
            data = self.adc.rx()  # Receive the data
            for ch in range(0, len(data)):
                self.q.put(data[ch])

    def plot(self):
        """Plot the data in queue after certain time if data collection method is plot"""
        x = np.arange(0, N)
        while not self.q.empty():
            plt.ion()
            for ch in range(len(self.adc._ctrl.channels)):
                wf_data = self.q.get()
                if self.adc._ctrl.channels == signal_to_plot:
                    plt.figure(self.adc._ctrl.channels[ch]._name)
                    plt.clf()
                    plt.step(x * (1000 / fs), wf_data)
            plt.draw()

    def log(self):
        """Log the data to a csv file if data collection method is log"""

        if len(self.adc._ctrl.channels) == 2:
            d = ["differential0", "differential1"]
        else:
            d = ["differential0", "common0", "differential1", "common1"]

        df = pd.DataFrame(columns=d)  # create a dataframe with the headings of column
        df.to_csv("example.csv", index=False)  # write the header to a csv file

        while (
            not self.q.empty()
        ):  # Run till q is empty that is we write all the sampled data to file

            if len(self.adc._ctrl.channels) == 2:  # if 24bit or 30bit diff mode
                differential0 = self.q.get()  # Pop data out of queue
                differential1 = self.q.get()

                diff0 = pd.Series(
                    differential0
                )  # Convert list of data as row to column of data in pandas dataframe
                diff1 = pd.Series(differential1)

                df[
                    "differential0"
                ] = diff0  # assign differential0  header with the above column of data
                df["differential1"] = diff1

            else:
                differential0 = self.q.get()
                common0 = self.q.get()
                differential1 = self.q.get()
                common1 = self.q.get()

                diff0 = pd.Series(differential0)
                cmn0 = pd.Series(common0)
                diff1 = pd.Series(differential1)
                cmn1 = pd.Series(common1)

                df["differential0"] = diff0
                df["common0"] = cmn0
                df["differential1"] = diff1
                df["common1"] = cmn1

            # append all the column with data and write it to csv file
            df.to_csv("example.csv", index=False, mode="a", header=False)


if __name__ == "__main__":

    app = ad463x_plot()
