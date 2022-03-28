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


# This example configures and the Rx/Tx frequency hopping NCOs.
# Later these configurations are selected either via SPI registers or by using external GPIO select.

import sys
import time

import adi
import matplotlib.pyplot as plt
import numpy as np
from adi.one_bit_adc_dac import one_bit_adc_dac
from scipy import signal

dev = adi.ad9081("ip:10.44.3.53")
gpio = adi.one_bit_adc_dac("ip:10.44.3.53")

# Total number of CDDCs/CDUCs
NM_RX = len(dev.rx_main_nco_frequencies)
NM_TX = len(dev.tx_main_nco_frequencies)

dev.tx_main_nco_frequencies = [500000000] * 4

dev.tx_main_ffh_gpio_mode_enable = 0
dev.tx_main_ffh_mode = ["phase_coherent"] * NM_TX

dev.rx_main_ffh_mode = ["instantaneous_update"] * NM_RX
dev.rx_main_ffh_trig_hop_en = [0] * NM_RX

for i in range(16):
    dev.rx_main_nco_ffh_index = [i] * NM_RX
    dev.rx_main_nco_frequencies = [500000000 + i * 1000000] * NM_RX

for i in range(31):
    dev.tx_main_ffh_index = [i] * NM_TX
    dev.tx_main_ffh_frequency = [500000000 + i * 1000000] * NM_TX
    # print (dev.tx_main_ffh_frequency)

# Select Rx/Tx NCO channels via register control
if False:
    for _ in range(1000):
        for i in range(16):
            dev.rx_main_nco_ffh_select = [i] * NM_RX
            dev.tx_main_nco_ffh_select = [i] * NM_RX
            time.sleep(0.1)

# Select Tx FFH NCOs using Tx GPIOs (DAC_NCO_FFHx, DAC_NCO_FFH_STROBE)
if False:
    # select NCO0
    gpio.gpio_gpio_syncin1n = 0
    gpio.gpio_gpio_syncin1p = 1

    gpio.gpio_gpio_syncout1n = 0
    gpio.gpio_gpio_syncout1p = 1

    dev.tx_main_ffh_gpio_mode_enable = 1
    for _ in range(1000):
        for i in range(32):
            # Tx NCO
            gpio.gpio_gpio_0 = i & 0x1
            gpio.gpio_gpio_1 = i & 0x2
            gpio.gpio_gpio_2 = i & 0x4
            gpio.gpio_gpio_3 = i & 0x8
            gpio.gpio_gpio_4 = i & 0x10
            gpio.gpio_gpio_5 = 0
            gpio.gpio_gpio_5 = 1
            # Rx NCO
            gpio.gpio_gpio_6 = i & 0x1
            gpio.gpio_gpio_7 = i & 0x2
            gpio.gpio_gpio_8 = i & 0x4
            gpio.gpio_gpio_9 = i & 0x8
            time.sleep(0.1)

dev.rx_enabled_channels = [0]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = ["odd"] * NM_RX

dev.rx_buffer_size = 2 ** 16
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sample_rate)

# Set single DDS tone for TX on one transmitter
# dev.dds_single_tone(fs / 100, 0.5, channel=0)

dev.dds_enabled = [1] * 32
dev.dds_frequencies = [fs / 100] * 32
dev.dds_scales = [0.5] * 32


# Loop through 16 Tx/Rx corresponding NCO configuration,
# make sure the spectral peak doesn’t move
for i in range(1000):
    for r in range(16):
        dev.rx_main_nco_ffh_select = [r] * NM_RX
        dev.tx_main_nco_ffh_select = [r] * NM_TX
        x = dev.rx()

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
