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
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from cn0566_functions import (
    calculate_plot,
    gain_calibration,
    load_hb100_cal,
    phase_calibration,
)
from scipy import signal

failures = []
monitor_hi_limits = [60.0, 1.9, 3.015, 3.45, 4.75, 16.0, 5.50, 99.0, 16.0]
monitor_lo_limts = [20.0, 1.8, 2.850, 3.15, 0.00, 00.0, 0.00, 0.0, 0.0]
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

gain_cal_limits = (
    0.70  # Fail if any channel is less than 60% of the highest gain channel
)
phase_cal_limits = (
    80.0  # Fail if delta between any two channels is more than 50 degress.
)

if os.name == "nt":  # Assume running on Windows
    rpi_ip = "ip:phaser.local"  # IP address of the remote Raspberry Pi
    sdr_ip = "ip:pluto.local"  # Pluto IP, with modified IP address or not
    print("Running on Windows, connecting to ", rpi_ip, " and ", sdr_ip)
elif os.name == "posix":
    rpi_ip = "ip:localhost"  # Assume running locally on Raspberry Pi
    sdr_ip = "ip:192.168.2.1"  # Historical - assume default Pluto IP
    print("Running on Linux, connecting to ", rpi_ip, " and ", sdr_ip)
else:
    print("Can't detect OS")


try:
    x = my_sdr.uri
    print("Pluto already connected")
except NameError:
    print("Pluto not connected, connecting...")
    from adi import ad9361

    my_sdr = ad9361(uri=sdr_ip)

time.sleep(0.5)

try:
    x = my_cn0566.uri
    print("cn0566 already connected")
except NameError:
    print("cn0566 not connected, connecting...")
    from adi.cn0566 import CN0566

    my_cn0566 = CN0566(uri=rpi_ip, rx_dev=my_sdr)


# Set up receive frequency. When using HB100, you need to know its frequency
# fairly accurately. Use the cn0566_find_hb100.py script to measure its frequency
# and write out to the cal file. IF using the onboard TX generator, delete
# the cal file and set frequency via config.py or config_custom.py.

try:
    my_cn0566.SignalFreq = load_hb100_cal()
    print("Found signal freq file, ", my_cn0566.SignalFreq)
except:
    my_cn0566.SignalFreq = 10.525e9
    print("No signal freq found, keeping at ", my_cn0566.SignalFreq)

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

my_sdr.rx_lo = int(2.2e9)  # 4495000000  # Recieve Freq
my_sdr.tx_lo = int(2.2e9)

my_sdr.filter = "LTE20_MHz.ftr"  # MWT: Using this for now, may not be necessary.
rx_buffer_size = int(4 * 256)
my_sdr.rx_buffer_size = rx_buffer_size

my_sdr.tx_cyclic_buffer = True
my_sdr.tx_buffer_size = int(2 ** 16)

my_sdr.tx_hardwaregain_chan0 = int(-88)  # this is a negative number between 0 and -88
my_sdr.tx_hardwaregain_chan1 = int(
    -6
)  # Make sure the Tx channels are attenuated (or off) and their freq is far away from Rx

# my_sdr.dds_enabled = [1, 1, 1, 1] #DDS generator enable state
# my_sdr.dds_frequencies = [0.1e6, 0.1e6, 0.1e6, 0.1e6] #Frequencies of DDSs in Hz
# my_sdr.dds_scales = [1, 1, 0, 0] #Scale of DDS signal generators Ranges [0,1]
my_sdr.dds_single_tone(
    int(2e6), 0.9, 1
)  # sdr.dds_single_tone(tone_freq_hz, tone_scale_0to1, tx_channel)

#  Configure CN0566 parameters.
#     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
#     accessed through other methods.

# By default device_mode is "rx"
my_cn0566.configure(
    device_mode="rx"
)  # Configure adar in mentioned mode and also sets gain of all channel to 127


# Onboard source w/ external Vivaldi
my_cn0566.frequency = (
    int(my_cn0566.SignalFreq) + my_sdr.rx_lo
) // 4  # PLL feedback via /4 VCO output
my_cn0566.freq_dev_step = 5690
my_cn0566.freq_dev_range = 0
my_cn0566.freq_dev_time = 0
my_cn0566.powerdown = 0
my_cn0566.ramp_mode = "disabled"


# MWT: Do NOT need to load in cal values during production test.
# my_cn0566.load_gain_cal('gain_cal_val.pkl')
# my_cn0566.load_phase_cal('phase_cal_val.pkl')

# Averages decide number of time samples are taken to plot and/or calibrate system. By default it is 1.
my_cn0566.Averages = 8


print("Reading voltage monitor...")
monitor_vals = my_cn0566.read_monitor()

for i in range(0, len(monitor_vals)):
    if not (monitor_lo_limts[i] <= monitor_vals[i] <= monitor_hi_limits[i]):
        print("Fails ", monitor_ch_names[i], ": ", monitor_vals[i])
        failures.append(monitor_ch_names[i])
    else:
        print("Passes ", monitor_ch_names[i], monitor_vals[i])

print("ToDo: Compare monitor readings with allowable (TBD) minimums and maximums.")


print(
    "Calibrating gain and phase - place antenna at mechanical boresight in front\
      of the array, then press enter..."
)
print("Calibrating Gain, verbosely, then saving cal file...")
gain_calibration(my_cn0566, verbose=True)  # Start Gain Calibration

print("Calibrating Phase, verbosely, then saving cal file...")
phase_calibration(my_cn0566, verbose=True)  # Start Phase Calibration

print("Done calibration")


# my_cn0566.save_gain_cal()  # Default filename
# my_cn0566.save_phase_cal()  # Default filename

for i in range(0, len(my_cn0566.gcal)):
    if my_cn0566.gcal[i] < gain_cal_limits:
        print("Gain cal failure on element ", i, ", ", my_cn0566.gcal[i])
        failures.append(
            "Gain cal falure on element "
        )  # + str(i)) # Throws isort error?


for i in range(0, len(my_cn0566.pcal)):
    if abs(my_cn0566.pcal[i]) > phase_cal_limits:
        print("Phase cal failure on element ", i, ", ", my_cn0566.pcal[i])
        failures.append("Phase cal falure on element ")  # + str(i))

if len(failures) == 0:
    print("WooHoo! BOARD PASSES!!")
else:
    print("D'oh! BOARD FAILS!")
    for failure in failures:
        print(failure)
    print("\n\n")


do_plot = (
    True  # Do a plot just for debug purposes. Suppress for actual production test.
)

while do_plot == True:

    start = time.time()
    my_cn0566.set_beam_phase_diff(0.0)
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
    ) = calculate_plot(my_cn0566)
    print("Sweeping took this many seconds: " + str(time.time() - start))
    #    gain,  = my_cn0566.plot(plot_type="monopulse")
    plt.clf()
    plt.scatter(angle, gain, s=10)
    plt.scatter(angle, delta, s=10)
    plt.show()

    plt.pause(0.05)
    time.sleep(0.05)
    print("Total took this many seconds: " + str(time.time() - start))

    do_plot = False
    print("Exiting Loop")
