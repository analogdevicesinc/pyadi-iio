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


# Basic utility script for working with the CN0566 "Phaser" board. Accepts the following
# command line arguments:

# plot - plot beam pattern, rectangular element weighting. If cal files are present,
#        they will be loaded.

# cal - perform both gain and phase calibration, save to files.

import sys
import time
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
from adi import ad9361
from adi.cn0566 import CN0566
from phaser_functions import (
    calculate_plot,
    channel_calibration,
    gain_calibration,
    load_hb100_cal,
    phase_calibration,
)
from scipy import signal

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

colors = ["black", "gray", "red", "orange", "yellow", "green", "blue", "purple"]


def do_cal_channel():
    my_phaser.set_beam_phase_diff(0.0)
    channel_calibration(my_phaser, verbose=True)


def do_cal_gain():
    my_phaser.set_beam_phase_diff(0.0)
    #    plot_data = my_phaser.gain_calibration(verbose=True)  # Start Gain Calibration
    plot_data = gain_calibration(my_phaser, verbose=True)  # Start Gain Calibration
    plt.figure(4)
    plt.title("Gain calibration FFTs")
    plt.xlabel("FFT Bin number")
    plt.ylabel("Amplitude (ADC counts)")
    for i in range(0, 8):
        plt.plot(plot_data[i], color=colors[i])
    plt.show()


def do_cal_phase():
    # PhaseValues, plot_data = my_phaser.phase_calibration(
    #     verbose=True
    # )  # Start Phase Calibration
    PhaseValues, plot_data = phase_calibration(
        my_phaser, verbose=True
    )  # Start Phase Calibration
    plt.figure(5)
    plt.title("Phase sweeps of adjacent elements")
    plt.xlabel("Phase difference (degrees)")
    plt.ylabel("Amplitude (ADC counts)")
    for i in range(0, 7):
        plt.plot(PhaseValues, plot_data[i], color=colors[i])
    plt.show()


# First try to connect to a locally connected CN0566. On success, connect,
# on failure, connect to remote CN0566

try:
    print("Attempting to connect to CN0566 via ip:localhost...")
    my_phaser = CN0566(uri="ip:localhost")
    print("Found CN0566. Connecting to PlutoSDR via default IP address...")
    my_sdr = ad9361(uri="ip:192.168.2.1")
    print("PlutoSDR connected.")

except:
    print("CN0566 on ip.localhost not found, connecting via ip:phaser.local...")
    my_phaser = CN0566(uri="ip:phaser.local")
    print("Found CN0566. Connecting to PlutoSDR via shared context...")
    my_sdr = ad9361(uri="ip:phaser.local:50901")
    print("Found SDR on shared phaser.local.")

my_phaser.sdr = my_sdr  # Set my_phaser.sdr

time.sleep(0.5)


# By default device_mode is "rx"
my_phaser.configure(device_mode="rx")


my_phaser.SDR_init(30000000, config.Tx_freq, config.Rx_freq, 6, -6, 1024)

my_phaser.load_channel_cal()
# First crack at compensating for channel gain mismatch
my_phaser.sdr.rx_hardwaregain_chan0 = (
    my_phaser.sdr.rx_hardwaregain_chan0 + my_phaser.ccal[0]
)
my_phaser.sdr.rx_hardwaregain_chan1 = (
    my_phaser.sdr.rx_hardwaregain_chan1 + my_phaser.ccal[1]
)

# Set up receive frequency. When using HB100, you need to know its frequency
# fairly accurately. Use the cn0566_find_hb100.py script to measure its frequency
# and write out to the cal file. IF using the onboard TX generator, delete
# the cal file and set frequency via config.py or config_custom.py.

try:
    my_phaser.SignalFreq = load_hb100_cal()
    print("Found signal freq file, ", my_phaser.SignalFreq)
except:
    my_phaser.SignalFreq = config.SignalFreq
    print("No signal freq found, keeping at ", my_phaser.SignalFreq)
    print("And using TX path. Make sure antenna is connected.")
    config.use_tx = True  # Assume no HB100, use TX path.

#  Configure SDR parameters.

my_sdr.filter = "LTE20_MHz.ftr"  # Load LTE 20 MHz filter


# use_tx = config.use_tx
use_tx = True

if use_tx is True:
    # To use tx path, set chan1 gain "high" keep chan0 attenuated.
    my_sdr.tx_hardwaregain_chan0 = int(
        -88
    )  # this is a negative number between 0 and -88
    my_sdr.tx_hardwaregain_chan1 = int(-3)
    my_sdr.tx_lo = config.Tx_freq  # int(2.2e9)

    my_sdr.dds_single_tone(
        int(2e6), 0.9, 1
    )  # sdr.dds_single_tone(tone_freq_hz, tone_scale_0to1, tx_channel)
else:
    # To disable rx, set attenuation to a high value and set frequency far from rx.
    my_sdr.tx_hardwaregain_chan0 = int(
        -88
    )  # this is a negative number between 0 and -88
    my_sdr.tx_hardwaregain_chan1 = int(-88)
    my_sdr.tx_lo = int(1.0e9)


# Configure CN0566 parameters.
#     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
#     accessed through other methods.


# my_phaser.frequency = (10492000000 + 2000000000) // 4 #6247500000//2

# Onboard source w/ external Vivaldi
my_phaser.frequency = (
    int(my_phaser.SignalFreq) + config.Rx_freq
) // 4  # PLL feedback via /4 VCO output
my_phaser.freq_dev_step = 5690
my_phaser.freq_dev_range = 0
my_phaser.freq_dev_time = 0
my_phaser.powerdown = 0
my_phaser.ramp_mode = "disabled"

#  If you want to use previously calibrated values load_gain and load_phase values by passing path of previously
#  stored values. If this is not done system will be working as uncalibrated system.
#  These will fail gracefully and default to no calibration if files not present.

my_phaser.load_gain_cal("gain_cal_val.pkl")
my_phaser.load_phase_cal("phase_cal_val.pkl")

# This can be useful in Array size vs beam width experiment or beamtappering experiment.
#     Set the gain of outer channels to 0 and beam width will increase and so on.

# To set gain of all channels with different values.
#     Here's where you would apply a window / taper function,
#     but we're starting with rectangular / SINC1.

gain_list = [127, 127, 127, 127, 127, 127, 127, 127]
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

# Averages decide number of time samples are taken to plot and/or calibrate system. By default it is 1.
my_phaser.Averages = 4

# Aim the beam at boresight by default
my_phaser.set_beam_phase_diff(0.0)

# Really basic options - "plot" to plot continuously, "cal" to calibrate both gain and phase.
func = sys.argv[1] if len(sys.argv) >= 2 else "plot"


if func == "cal":
    input(
        "Calibrating gain and phase - place antenna at mechanical boresight in front of the array, then press enter..."
    )
    print("Calibrating gain mismatch between SDR channels, then saving cal file...")
    do_cal_channel()
    my_phaser.save_channel_cal()
    print("Calibrating Gain, verbosely, then saving cal file...")
    do_cal_gain()  # Start Gain Calibration
    my_phaser.save_gain_cal()  # Default filename
    print("Calibrating Phase, verbosely, then saving cal file...")
    do_cal_phase()  # Start Phase Calibration
    my_phaser.save_phase_cal()  # Default filename
    print("Done calibration")

if func == "plot":
    do_plot = True
else:
    do_plot = False

while do_plot == True:
    try:
        start = time.time()
        my_phaser.set_beam_phase_diff(0.0)
        time.sleep(0.25)
        data = my_sdr.rx()
        data = my_sdr.rx()
        ch0 = data[0]
        ch1 = data[1]
        f, Pxx_den0 = signal.periodogram(
            ch0[1:-1], 30000000, "blackman", scaling="spectrum"
        )
        f, Pxx_den1 = signal.periodogram(
            ch1[1:-1], 30000000, "blackman", scaling="spectrum"
        )

        plt.figure(1)
        plt.clf()
        plt.plot(np.real(ch0), color="red")
        plt.plot(np.imag(ch0), color="blue")
        plt.plot(np.real(ch1), color="green")
        plt.plot(np.imag(ch1), color="black")
        np.real
        plt.xlabel("data point")
        plt.ylabel("output code")
        plt.draw()

        plt.figure(2)
        plt.clf()
        plt.semilogy(f, Pxx_den0)
        plt.semilogy(f, Pxx_den1)
        plt.ylim([1e-5, 1e6])
        plt.xlabel("frequency [Hz]")
        plt.ylabel("PSD [V**2/Hz]")
        plt.draw()

        # Plot the output based on experiment that you are performing
        print("Plotting...")

        plt.figure(3)
        plt.ion()
        #    plt.show()
        (
            gain,
            angle,
            delta,
            diff_error,
            beam_phase,
            xf,
            max_gain,
            PhaseValues,
        ) = calculate_plot(my_phaser)
        print("Sweeping took this many seconds: " + str(time.time() - start))
        #    gain,  = my_phaser.plot(plot_type="monopulse")
        plt.clf()
        plt.scatter(angle, gain, s=10)
        plt.scatter(angle, delta, s=10)
        plt.show()

        plt.pause(0.05)
        time.sleep(0.05)
        print("Total took this many seconds: " + str(time.time() - start))
    except KeyboardInterrupt:
        do_plot = False
        print("Exiting Loop")

if func == "div_test":
    while True:
        my_phaser.set_tx_sw_div(0)
        sleep(1.0)
        my_phaser.set_tx_sw_div(2)
        sleep(1.0)
        my_phaser.set_tx_sw_div(4)
        sleep(1.0)
        my_phaser.set_tx_sw_div(8)
        sleep(1.0)
        my_phaser.set_tx_sw_div(16)
        sleep(1.0)
        my_phaser.set_tx_sw_div(32)
        sleep(1.0)
        my_phaser.set_tx_sw_div(64)
        sleep(1.0)
        my_phaser.set_tx_sw_div(128)
        sleep(1.0)
