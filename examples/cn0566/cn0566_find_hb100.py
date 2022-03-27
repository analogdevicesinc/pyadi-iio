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


# Utility script to find the frequency of an HB100 microwave source.
# Also serves as basic example for setting / stepping the frequency of
# the phaser's PLL, capturing data, calculating FFTs, and stitching together
# FFTs that span several bands.


import os
import sys
import time
from test.rf.spec import measure_peaks, spec_est

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

if os.name == "nt":  # Assume running on Windows
    rpi_ip = "ip:phaser.local"  # IP address of the remote Raspberry Pi
    #     rpi_ip = "ip:169.254.225.48" # Hard code an IP here for debug
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


#  Configure SDR parameters.
#     Current freq plan is Sig Freq = 10.492 GHz, antenna element spacing = 0.015m, Freq of pll is 12/2 GHz
#     this is mixed down using mixer to get 10.492 - 6 = 4.492GHz which is freq of sdr.
#     This frequency plan can be updated any time in example code
#     e.g:- my_cn0566.frequency = 9000000000 etc

# configure sdr/pluto according to above-mentioned freq plan

my_sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
my_sdr._ctrl.debug_attrs[
    "adi,ensm-enable-txnrx-control-enable"
].value = "0"  # Disable pin control so spi can move the states
my_sdr._ctrl.debug_attrs["initialize"].value = "1"

my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
my_sdr._rxadc.set_kernel_buffers_count(1)  # No stale buffers to flush
rx = my_sdr._ctrl.find_channel("voltage0")
rx.attrs[
    "quadrature_tracking_en"
].value = "1"  # set to '1' to enable quadrature tracking
my_sdr.sample_rate = int(30000000)  # Sampling rate
my_sdr.rx_buffer_size = int(4 * 256)
my_sdr.rx_rf_bandwidth = int(10e6)
# We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
my_sdr.gain_control_mode_chan0 = "manual"  # DISable AGC
my_sdr.gain_control_mode_chan1 = "manual"
my_sdr.rx_hardwaregain_chan0 = 20
my_sdr.rx_hardwaregain_chan1 = 20

my_sdr.rx_lo = int(2.0e9)  # Downconvert by 2GHz  # Recieve Freq

my_sdr.filter = "LTE20_MHz.ftr"  # MWT: Using this for now, may not be necessary.
rx_buffer_size = int(4 * 256)
my_sdr.rx_buffer_size = rx_buffer_size

my_sdr.tx_cyclic_buffer = True
my_sdr.tx_buffer_size = int(2 ** 16)

my_sdr.tx_hardwaregain_chan0 = int(-88)  # this is a negative number between 0 and -88
my_sdr.tx_hardwaregain_chan1 = int(
    -88
)  # Make sure the Tx channels are attenuated (or off) and their freq is far away from Rx

# my_sdr.dds_enabled = [1, 1, 1, 1] #DDS generator enable state
# my_sdr.dds_frequencies = [0.1e6, 0.1e6, 0.1e6, 0.1e6] #Frequencies of DDSs in Hz
# my_sdr.dds_scales = [1, 1, 0, 0] #Scale of DDS signal generators Ranges [0,1]
my_sdr.dds_single_tone(
    int(2e6), 0.9, 1
)  # sdr.dds_single_tone(tone_freq_hz, tone_scale_0to1, tx_channel)

# Configure CN0566 parameters.
#     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
#     accessed through other methods.

# By default device_mode is "rx"
my_cn0566.configure(
    device_mode="rx"
)  # Configure adar in mentioned mode and also sets gain of all channel to 127

# HB100 measured frequency - 10492000000

# my_cn0566.SignalFreq = 10600000000 # Make this automatic in the future.
my_cn0566.SignalFreq = 10.497e9

# my_cn0566.frequency = (10492000000 + 2000000000) // 4 #6247500000//2

# Onboard source w/ external Vivaldi
my_cn0566.frequency = (
    int(my_cn0566.SignalFreq) + my_sdr.rx_lo
) // 4  # PLL feedback via /4 VCO output
my_cn0566.freq_dev_step = 5690
my_cn0566.freq_dev_range = 0
my_cn0566.freq_dev_time = 0
my_cn0566.powerdown = 0
my_cn0566.ramp_mode = "disabled"

# Set all elements to maximum gain

gain_list = [127, 127, 127, 127, 127, 127, 127, 127]
for i in range(0, len(gain_list)):
    my_cn0566.set_chan_gain(i, gain_list[i], apply_cal=False)

# Averages decide number of time samples are taken to plot and/or calibrate system. By default it is 1.
my_cn0566.Averages = 8


full_ampl = np.empty(0)
full_freqs = np.empty(0)

# Set up range of frequencies to sweep. Sample rate is set to 30Msps,
# for a total of 30MHz of bandwidth (quadrature sampling)
# Filter is 20MHz LTE, so you get a bit less than 20MHz of usable
# bandwidth. Set step size to something less than 20MHz to ensure
# complete coverage.
f_start = 10.4e9
f_stop = 10.6e9
f_step = 10e6

for freq in range(int(f_start), int(f_stop), int(f_step)):
    print("frequency: ", freq)
    my_cn0566.SignalFreq = freq
    my_cn0566.frequency = (
        int(my_cn0566.SignalFreq) + my_sdr.rx_lo
    ) // 4  # PLL feedback via /4 VCO output

    data = my_sdr.rx()
    data_sum = data[0] + data[1]
    ampl, freqs = spec_est(data_sum, 30000000, ref=2 ^ 12, plot=False)
    ampl = np.fft.fftshift(ampl)
    ampl = np.flip(ampl)  # Just an experiment...
    freqs = np.fft.fftshift(freqs)
    freqs += freq
    full_freqs = np.concatenate((full_freqs, freqs))
    full_ampl = np.concatenate((full_ampl, ampl))
    # break
full_freqs /= 1e9

peak_index = np.argmax(full_ampl)
print("Peak frequency found at ", full_freqs[peak_index], " GHz.")

plt.figure(2)
plt.title("Full Spectrum, peak at " + str(full_freqs[peak_index]) + " GHz.")
plt.plot(full_freqs, full_ampl, linestyle="", marker="o", ms=2)
plt.xlabel("Frequency [GHz]")
plt.ylabel("Amplitude (dBfs)")
