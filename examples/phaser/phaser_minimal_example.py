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


# A minimal example script to demonstrate some basic concepts of controlling
# the Pluto SDR.
# The script reads in the measured HB100 source's frequency (previously stored
# with the find_hb100 utility), sets the phaser's pll such that the HB100's frequency
# shows up at 1MHz, captures a buffer of data, take FFT, plot time and frequency domain

# Since the Pluto is attached to the phaser board, we do have
# to do some setup and housekeeping of the ADAR1000s, but other than that it's
# trimmed down about as much as possible.

# Import libraries.
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
from adi import ad9361
from adi.cn0566 import CN0566
from phaser_functions import load_hb100_cal, spec_est

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

sleep(0.5)

# By default device_mode is "rx"
my_phaser.configure(device_mode="rx")

try:
    my_phaser.SignalFreq = load_hb100_cal()
    print("Found signal freq file, ", my_phaser.SignalFreq)
except:
    my_phaser.SignalFreq = 10.525e9
    print("No signal freq file found, setting to 10.525 GHz")


# Configure CN0566 parameters.
#     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
#     accessed through other methods.


# Set all antenna elements to half scale - a typical HB100 will have plenty
# of signal power.

gain_list = [64] * 8  # (64 is about half scale)
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=False)

# Aim the beam at boresight (zero degrees). Place HB100 right in front of array.
my_phaser.set_beam_phase_diff(0.0)


#  Configure SDR parameters. Start with the more involved settings, don't
# pay too much attention to these. They are covered in much more detail in
# Software Defined Radio for Engineers.

my_sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
my_sdr._ctrl.debug_attrs[
    "adi,ensm-enable-txnrx-control-enable"
].value = "0"  # Disable pin control so spi can move the states
my_sdr._ctrl.debug_attrs["initialize"].value = "1"

my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
my_sdr._rxadc.set_kernel_buffers_count(1)  # No stale buffers to flush
rx = my_sdr._ctrl.find_channel("voltage0")
rx.attrs["quadrature_tracking_en"].value = "1"  # enable quadrature tracking
# Make sure the Tx channels are attenuated (or off) and their freq is far away from Rx
# this is a negative number between 0 and -88
my_sdr.tx_hardwaregain_chan0 = int(-80)
my_sdr.tx_hardwaregain_chan1 = int(-80)


# These parameters are more closely related to analog radio design
# and are what you would adjust to change the IFs, signal bandwidths, sample rate, etc.
#
# Sample rate is set to 30Msps,
# for a total of 30MHz of bandwidth (quadrature sampling)
# Filter is 20MHz LTE, so you get a bit less than 20MHz of usable
# bandwidth.

my_sdr.sample_rate = int(30e6)  # Sampling rate
my_sdr.rx_buffer_size = int(1024)  # Number of samples per buffer
my_sdr.rx_rf_bandwidth = int(10e6)  # Analog bandwidth

# Manually control gain - in most applications, you want to enable AGC to keep
# to adapt to changing conditions. Since we're taking quasi-quantitative measurements,
# we want to set the gain to a fixed value.
my_sdr.gain_control_mode_chan0 = "manual"  # DISable AGC
my_sdr.gain_control_mode_chan1 = "manual"
my_sdr.rx_hardwaregain_chan0 = 0  # dB
my_sdr.rx_hardwaregain_chan1 = 0  # dB

my_sdr.rx_lo = int(2.2e9)  # Downconvert by 2GHz  # Receive Freq
my_sdr.filter = "LTE20_MHz.ftr"  # Handy filter for fairly widdeband measurements

# Now set the phaser's PLL. This is the ADF4159, and we'll set it to the HB100 frequency
# plus the desired 2GHz IF, minus a small offset so we don't land at exactly DC.
# If the HB100 is at exactly 10.525 GHz, setting the PLL to 12.724 GHz will result
# in an IF at 2.201 GHz.

offset = 1000000  # add a small offset
my_phaser.frequency = (
    int(my_phaser.SignalFreq + my_sdr.rx_lo - offset)
) // 4  # PLL feedback is from the VCO's /4 output

# Capture data!
data = my_sdr.rx()
# Add both channels for calculating spectrum
data_sum = data[0] + data[1]

# spec_est is a simple estimation function that applies a window, takes the FFT,
# scales and converts to dB.
ampl, freqs = spec_est(data_sum, 30e6, ref=2 ^ 12, plot=False)
ampl = np.fft.fftshift(ampl)
ampl = np.flip(ampl)  # Just an experiment...
freqs = np.fft.fftshift(freqs)

freqs /= 1e6  # Scale Hz -> MHz

peak_index = np.argmax(ampl)  # Locate the peak frequency's index
peak_freq = freqs[peak_index]  # And the frequency itself.
print("Peak frequency found at ", freqs[peak_index], " MHz.")

# Now plot the data
plt.figure(1)
plt.subplot(2, 1, 1)
plt.title("Time Domain I/Q Data")
plt.plot(data[0].real, marker="o", ms=2, color="red")  # Only plot real part
plt.plot(data[1].real, marker="o", ms=2, color="blue")
plt.xlabel("Data Point")
plt.ylabel("ADC output")
plt.subplot(2, 1, 2)
plt.title("Spectrum, peak at " + str(freqs[peak_index]) + " MHz.")
plt.plot(freqs, ampl, marker="o", ms=2)
plt.xlabel("Frequency [MHz]")
plt.ylabel("Signal Strength")
plt.tight_layout()
plt.show()

# Clean up / close connections
del my_sdr
del my_phaser
