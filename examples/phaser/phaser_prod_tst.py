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


# First cut at a production test. Just a template at this point.
# Read all board voltages, current, ambient temperature, and compare against limits

# Run gain calibration, verify signal levels are within some fairly wide limits,
# and that the spread between minimum and maximum gains is within TBD limits.

# Run phase calibration, verify that phase corretionn values are within TBD degrees.


# Also consider having a minimal board-level test just to verify basic functionality,
# with wider test limits. This would be run before assembling the entire phaser
# (with Pluto, Pi, Standoffs, etc.)


import os
import socket
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from adi import ad9361
from adi.cn0566 import CN0566
from phaser_functions import (
    calculate_plot,
    channel_calibration,
    gain_calibration,
    get_signal_levels,
    phase_calibration,
)
from scipy import signal

start = time.time()

failures = []
#                    temp   1.8V 3.0    3.3   4.5   15?   USB   curr. Vtune
monitor_hi_limits = [60.0, 1.85, 3.15, 3.45, 4.75, 16.0, 5.25, 1.6, 14.0]
monitor_lo_limts = [20.0, 1.75, 2.850, 3.15, 4.25, 13.0, 4.75, 1.2, 1.0]
monitor_ch_names = [
    "Board temperature: ",
    "1.8V supply: ",
    "3.0V supply: ",
    "3.3V supply: ",
    "4.5V supply: ",
    "Vtune amp supply: ",
    "USB C input supply: ",
    "Board current: ",
    "VTune: ",
]


channel_cal_limits = 10.0  # Fail if channels mismatched by more than 10 dB
gain_cal_limits = (
    0.50  # Fail if any channel is less than 60% of the highest gain channel
)
# Phase delta limits between channels. Extra tolerance between 3rd and 4th element,
# which split across the two Pluto channels.
phase_cal_limits = [90.0, 90.0, 90.0, 120.0, 90.0, 90.0, 90.0]

# Set up RF / IF / LO frequencies
rx_lo = 2.2e9
SignalFreq = 10.2e9

use_tx = True  # Use on board TX w/ cabled antenna, NOT external HB100


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

# Averages decide number of time samples are taken to plot and/or calibrate system. By default it is 1.
my_phaser.Averages = 8

# Set up receive frequency. When using HB100, you need to know its frequency
# fairly accurately. Use the cn0566_find_hb100.py script to measure its frequency
# and write out to the cal file. IF using the onboard TX generator, delete
# the cal file and set frequency via config.py or config_custom.py.

# Set the PLL once here, so that we can measure VTune below.
my_phaser.SignalFreq = SignalFreq
my_phaser.lo = int(SignalFreq) + rx_lo  # This actually sets the ADF4159.
time.sleep(0.5)  # Give the ADF4159 time to settle

# try:
#     my_phaser.SignalFreq = load_hb100_cal()
#     print("Found signal freq file, ", my_phaser.SignalFreq)
#     use_tx = False
# except:
#     my_phaser.SignalFreq = 10.525e9
#     print("No signal freq found, keeping at ", my_phaser.SignalFreq)
#     use_tx = True

# MWT: Do NOT load in cal values during production test. That's what we're doing, after all :)
# But running a second time with saved cal values may be useful in development.
# my_phaser.load_gain_cal('gain_cal_val.pkl')
# my_phaser.load_phase_cal('phase_cal_val.pkl')


print("Using TX output closest to tripod mount, 10.525 GHz for production test.")


#  Configure CN0566 parameters.
#     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
#     accessed through other methods.

print("Reading voltage monitor...")
monitor_vals = my_phaser.read_monitor()

for i in range(0, len(monitor_vals)):
    if not (monitor_lo_limts[i] <= monitor_vals[i] <= monitor_hi_limits[i]):
        print("Fails ", monitor_ch_names[i], ": ", monitor_vals[i])
        failures.append(
            "Monitor fails " + monitor_ch_names[i] + ": " + str(monitor_vals[i])
        )
    else:
        print("Passes ", monitor_ch_names[i], monitor_vals[i])

if len(failures) > 0:
    print("Fails one or more supply voltage tests. Please set board aside for debug.")
    sys.exit()
else:
    print("Passes all monitor readings, proceeding...")

if (monitor_vals[5] - monitor_vals[8]) < 1:
    print("Warning: Less than 1V headroom on Vtune")


print("\nSetting up Pluto and Getting signal levels...")
success = False
attempts = 0
max_attempts = 5

while attempts < max_attempts and not success:
    try:
        my_phaser.lo = int(SignalFreq) + rx_lo  # This actually sets the ADF4159.
        time.sleep(0.5)  # Give the ADF4159 time to settle

        # Configure SDR parameters.

        # configure sdr/pluto according to above-mentioned freq plan
        # my_sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
        # my_sdr._ctrl.debug_attrs["adi,ensm-enable-txnrx-control-enable"].value = "0"  # Disable pin control so spi can move the states
        # my_sdr._ctrl.debug_attrs["initialize"].value = "1"
        my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
        my_sdr._rxadc.set_kernel_buffers_count(
            1
        )  # Super important - don't want to have to flush stale buffers
        rx = my_sdr._ctrl.find_channel("voltage0")
        rx.attrs[
            "quadrature_tracking_en"
        ].value = "1"  # set to '1' to enable quadrature tracking
        my_sdr.sample_rate = int(30000000)  # Sampling rate
        my_sdr.rx_buffer_size = int(4 * 256)
        my_sdr.rx_rf_bandwidth = int(10e6)
        # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
        my_sdr.gain_control_mode_chan0 = "manual"
        my_sdr.gain_control_mode_chan1 = "manual"
        my_sdr.rx_hardwaregain_chan0 = 12
        my_sdr.rx_hardwaregain_chan1 = 12

        my_sdr.rx_lo = int(rx_lo)  # 4495000000  # Receive Freq

        print("Loading filter")
        my_sdr.filter = (
            os.getcwd() + "/LTE20_MHz.ftr"
        )  # MWT: Using this for now, may not be necessary.
        rx_buffer_size = int(4 * 256)
        my_sdr.rx_buffer_size = rx_buffer_size

        my_sdr.tx_cyclic_buffer = True
        my_sdr.tx_buffer_size = int(2 ** 16)

        if use_tx is True:
            # To disable rx, set attenuation to a high value and set frequency far from rx.
            my_sdr.tx_hardwaregain_chan0 = int(
                -88
            )  # this is a negative number between 0 and -88
            my_sdr.tx_hardwaregain_chan1 = int(-3)
            my_sdr.tx_lo = int(2.2e9)
        else:
            # To disable rx, set attenuation to a high value and set frequency far from rx.
            my_sdr.tx_hardwaregain_chan0 = int(
                -88
            )  # this is a negative number between 0 and -88
            my_sdr.tx_hardwaregain_chan1 = int(-88)
            my_sdr.tx_lo = int(1.0e9)

        # my_sdr.dds_enabled = [1, 1, 1, 1] #DDS generator enable state
        # my_sdr.dds_frequencies = [0.1e6, 0.1e6, 0.1e6, 0.1e6] #Frequencies of DDSs in Hz
        # my_sdr.dds_scales = [1, 1, 0, 0] #Scale of DDS signal generators Ranges [0,1]
        my_sdr.dds_single_tone(
            int(0.5e6), 0.9, 1
        )  # sdr.dds_single_tone(tone_freq_hz, tone_scale_0to1, tx_channel)

        sig_levels = get_signal_levels(my_phaser)
        print(sig_levels)
        if min(sig_levels) < 80.0:
            print("Low signal levels on attempt ", attempts, " of ", max_attempts)
            attempts += 1
        else:
            success = True
        if attempts == max_attempts:
            raise Exception("Max attempts reached")
    except:
        print(
            "failed after " + str(max_attempts) + " attempts, please set board aside."
        )
        sys.exit()


print(
    "Calibrating SDR channel mismatch, gain and phase - place antenna at "
    "mechanical boresight in front of the array.\n\n"
)


print("\nCalibrating SDR channel mismatch, verbosely...")
channel_calibration(my_phaser, verbose=True)

print("\nCalibrating Gain, verbosely, then saving cal file...")
gain_calibration(my_phaser, verbose=True)  # Start Gain Calibration

print("\nCalibrating Phase, verbosely, then saving cal file...")
phase_calibration(my_phaser, verbose=True)  # Start Phase Calibration

print("Done calibration")


# my_phaser.save_gain_cal()  # Default filename
# my_phaser.save_phase_cal()  # Default filename

for i in range(0, len(my_phaser.ccal)):
    if my_phaser.ccal[i] > channel_cal_limits:
        print("Channel cal failure on channel ", i, ", ", my_phaser.gcal[i])
        failures.append("Channel cal failure on channel " + str(i))

for i in range(0, len(my_phaser.gcal)):
    if my_phaser.gcal[i] < gain_cal_limits:
        print("Gain cal failure on element ", i, ", ", my_phaser.gcal[i])
        failures.append("Gain cal failure on element " + str(i))


# Important - my_phaser.pcal represents the CUMULATIVE phase shift across the
# array. Element 0 will always be zero, so we just need to check the delta between
# 0-1, 1-2, 2-3, etc. This IS sort of un-doing what the pcal routine does, but oh well...

for i in range(0, len(my_phaser.pcal) - 1):
    delta = my_phaser.pcal[i + 1] - my_phaser.pcal[i]
    if abs(delta) > phase_cal_limits[i]:
        print("Phase cal failure on elements ", i - 1, ", ", i, str(delta))
        failures.append(
            "Phase cal failure on elements "
            + str(i - 1)
            + ", "
            + str(i)
            + ", delta: "
            + str(delta)
        )

print("Test took " + str(time.time() - start) + " seconds.")

if len(failures) == 0:
    print("\nWooHoo! BOARD PASSES!!\n")
else:
    print("\nD'oh! BOARD FAILS!\n")
    for failure in failures:
        print(failure)
    print("\n\n")


ser_no = input("Please enter serial number of board, then press enter.\n")
filename = str("results/CN0566_" + ser_no + "_" + time.asctime() + ".txt")
filename = filename.replace(":", "-")
filename = os.getcwd() + "/" + filename

with open(filename, "w") as f:
    f.write("Phaser Test Results:\n")
    f.write("\nMonitor Readings:\n")
    f.write(str(monitor_vals))
    f.write("\nSignal Levels:\n")
    f.write(str(sig_levels))
    f.write("\nChannel Calibration:\n")
    f.write(str(my_phaser.ccal))
    f.write("\nGain Calibration:\n")
    f.write(str(my_phaser.gcal))
    f.write("\nPhase Calibration:\n")
    f.write(str(my_phaser.pcal))
    if len(failures) == 0:
        f.write("\nThis is a PASSING board!\n")
    else:
        f.write("\nThis is a FAILING board!\n")

do_plot = (
    False  # Do a plot just for debug purposes. Suppress for actual production test.
)

while do_plot == True:

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

    do_plot = False
    print("Exiting Loop")
