# Copyright (C) 2025 Analog Devices, Inc.
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

import sys
import time
from time import sleep

import matplotlib.pyplot as plt
import numpy as np

from adi import ad4080, ad9508, adf4350, one_bit_adc_dac

# Optionally pass URI as command line argument,
# else use default ip:analog.local

if len(sys.argv) < 3:
    print("Usage: script.py <my_uri> <Fsamp> [FiltMode] [DecRate]")
    sys.exit(1)

# Read input arguments
my_uri = sys.argv[1]  # First argument: URI
Fsamp = float(sys.argv[2])  # Second argument: Sampling Frequency (converted to float)
FiltMode = sys.argv[3]
DecRate = sys.argv[4]

my_adc = ad4080(uri=my_uri)
my_divider = ad9508(uri=my_uri, device_name="ad9508")
my_one_bit_adc_dac = one_bit_adc_dac(uri=my_uri)
my_pll = adf4350(uri=my_uri, device_name="/axi/spi@e0007000/adf4350@1")
# my_adc.rx_buffer_size = 2 ** 13

print("ad4080 sampling frequency: ", my_adc.sampling_frequency)

print("ad9508 channel 0 frequency: ", my_divider.channel[0].frequency)

print("pll adf4350 frequency: ", my_pll.frequency_altvolt0)

print("one bit adc dac sync n value", my_one_bit_adc_dac.gpio_sync_n)

print("ad4080 reg read", my_adc.reg_read(0x15))

print("Scale: ", my_adc.scale)

# Calculate adf4350 clock frequency
adf4350_clk = int(Fsamp * 10_000_000)  # Multiply by 10 million

## Disable the AD9508 outputs
my_one_bit_adc_dac.gpio_sync_n = 1

my_divider.reg_write(0x2B, 0x16)

if 200_000_000 <= adf4350_clk <= 430_000_000:
    adf4350_clk = adf4350_clk * 1
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 10
    my_divider.channel[3] = adf4350_clk / 1

    my_divider.reg_write(0x2B, 0x26)
    my_adc.reg_write(0x16, 0x51)

elif 100_000_000 <= adf4350_clk < 200_000_000:
    adf4350_clk = adf4350_clk * 2
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 20
    my_divider.channel[3] = adf4350_clk / 2

    my_adc.reg_write(0x16, 0x21)

elif 50_000_000 <= adf4350_clk < 100_000_000:
    adf4350_clk = adf4350_clk * 4
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 40
    my_divider.channel[3] = adf4350_clk / 4

    my_adc.reg_write(0x16, 0x21)

elif 25_000_000 <= adf4350_clk < 50_000_000:
    adf4350_clk = adf4350_clk * 8
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 80
    my_divider.channel[3] = adf4350_clk / 8

    my_adc.reg_write(0x16, 0x21)

elif 10_000_000 <= adf4350_clk < 25_000_000:
    adf4350_clk = adf4350_clk * 16
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 160
    my_divider.channel[3] = adf4350_clk / 16

    my_adc.reg_write(0x16, 0x21)

else:
    adf4350_clk = 400_000_000
    adf4350_clk = adf4350_clk * 1
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for: 40MSPS to 20MSPS Range")
    my_divider.channel[2] = adf4350_clk / 10
    my_divider.channel[3] = adf4350_clk / 1

    my_adc.reg_write(0x16, 0x41)

my_one_bit_adc_dac.gpio_sync_n = 0

# my_adc.filter_sel = "disabled"
time.sleep(0.25)
my_adc.lvds_sync = "enable"
time.sleep(0.25)
# my_adc.filter_sel = FiltMode
# time.sleep(0.25)
# my_adc.sinc_dec_rate = DecRate
# time.sleep(0.25)

plt.clf()
sleep(0.5)
data = my_adc.rx()

plt.plot(range(0, len(data)), data, label="channel0")
plt.xlabel("Data Point")
plt.ylabel("ADC counts")
plt.legend(
    bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
    loc="lower left",
    ncol=4,
    mode="expand",
    borderaxespad=0.0,
)

plt.show()
del my_adc
