# Copyright (C) 2023 Analog if_devices, Inc.
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

import time

import adi
import matplotlib.pyplot as plt
from scipy import signal

# Set up MxFE chip to receive Intermediate Frequency of 4.5 GHz (refer to ad9081_example.py)
if_dev = adi.ad9081(uri="ip:analog.local")
print("--Setting up MxFE chip")

# Configure RX properties
# Taking ADC Frequency = 6000 MHz, Main Decimation = 4 and Channel Decimation = 1 (refer to dts file for these values)
if_dev.rx_channel_nco_frequencies = [0] * 2
if_dev.rx_main_nco_frequencies = [1000000000, 0]
if_dev.rx_enabled_channels = [0]
# 4500 MHz lies in second (even) Nyquist zone
if_dev.rx_nyquist_zone = ["even"] * 2
if_dev.rx_buffer_size = 2 ** 16

# fs = RX Sample Rate = ADC Freq / (Main Decimation x Channel Decimation) = 6000/(4x1) = 1500 MHz
fs = int(if_dev.rx_sample_rate)

# Set up RF front end system and configure properties
rf_system = adi.xmw_rx_platform(uri="ip:analog.local")
print("--Setting up RF platform")

# Set up IF Attenuation (0dB)
rf_system.if_attenuation_decimal = 0

# Set up Input Attenuation (0dB)
rf_system.input_attenuation_dB = 0

# Set up Input Frequency Range
rf_system.input_freq_MHz = 12500

# Set up Input Mode (Through Preselector Bandpass Filter)
rf_system.input_mode = 1

# Observe IF on Spectrum Analyzer then digitized tone on plot
print(
    "Observe IF output from the RF front end system at 4500 MHz on the Spectrum Analyzer."
)
print(f"ADC Frequency: {if_dev.adc_frequency / 1000000} MHz.")
print(
    f"NCO frequency shift on Channel 0: {if_dev.rx_main_nco_frequencies[0] / 1000000} GHz."
)
print(
    f"IF of 4500 MHz is aliased into first Nyquist zone (4500 - ADC Frequency/2) and shifted by NCO Frequency Shift to {4500 - (if_dev.adc_frequency / 1000000) / 2 - if_dev.rx_main_nco_frequencies[0] / 1000000} MHz."
)
input(
    "Reconnect IF to ADC0 on the MxFE and press Enter to see a plot of the digitized tone at the above frequency."
)

# Collect data
for r in range(20):
    x = if_dev.rx()

    f, Pxx_den = signal.periodogram(x, fs, return_onesided=False)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e5])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
