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

import math
import time
from time import sleep

from ad4080_data_analysis import process_adc_raw_data

from adi import ad4080, ad9508, adf4350, one_bit_adc_dac

my_uri = "ip:analog.local"  # Default URI

Fsamp = 40e6  # Default Sampling Frequency entered in Hz
# Filter Mode options: "disabled", "sinc1", "sinc5", "sinc5_plus_compensation"
FiltMode = "disabled"
# Set Decimation Rate Options: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024
# Refer to Datasheet for options available to each Filter Mode
# This setting is ignored when FiltMode = "disabled"
DecRate = 2


my_adc = ad4080(uri=my_uri)
print("Scale: ", my_adc.scale)
sleep(0.5)  # Needed some delays
my_adc.reg_write(0x0A, 0xAA)
print("SPI Scratchpad Write Test, Read 0xAA: ", my_adc.reg_read(0x0A))
my_adc.reg_write(0x0A, 0x55)
print("SPI Scratchpad Write Test, Read 0x55: ", my_adc.reg_read(0x0A))
my_adc.reg_write(0x0A, 0x00)
print("SPI Scratchpad Write Test, Read 0x0: ", my_adc.reg_read(0x0A))
my_pll = adf4350(uri=my_uri, device_name="/axi/spi@e0007000/adf4350@1")
sleep(0.5)  # Needed some delays
my_divider = ad9508(uri=my_uri, device_name="ad9508")
sleep(0.5)  # Needed some delays
my_one_bit_adc_dac = one_bit_adc_dac(uri=my_uri)

# Setting how many conversions results to take
my_acq_size = 2 ** 18
my_adc.rx_buffer_size = my_acq_size

# Calculate adf4350 clock frequency
adf4350_clk = int(
    Fsamp * 10
)  # Multiply by 10x i.e. 10 CLKs per conversion for single lane LVDS
print("Requested ADC CNV clock frequency: ", Fsamp)
print("Requested LVDS CLK clock frequency: ", adf4350_clk)
# Disable the AD9508 outputs
my_one_bit_adc_dac.gpio_sync_n = 1
time.sleep(0.25)

# Determines what LVDS_CNV_CLK_CNT Reg (Addr 0x16) setting is required
def calc_clk_cnt(adf4350_clk):
    # Calculation for Single Lane LVDS with Gain Correction Off
    tMSB = 18e-9  # Datasheet specification for AD4080 with Gain Off
    CLK = adf4350_clk
    tCLK = 1 / CLK
    LVDS_CNV_CLK_CNT_num = math.floor((tMSB / tCLK) + 1.5)
    # print(LVDS_CNV_CLK_CNT_num)
    LVDS_CNV_CLK_CNT_reg = LVDS_CNV_CLK_CNT_num - 3  # True for Single Lane LVDS
    if LVDS_CNV_CLK_CNT_reg < 0:
        LVDS_CNV_CLK_CNT_reg = 0
    # print(LVDS_CNV_CLK_CNT_reg)
    lvds_reg_setting = (LVDS_CNV_CLK_CNT_reg << 4) + 1
    # print(hex(lvds_reg_setting))
    return lvds_reg_setting


# Case Statement to determine the ad9508 settings required.
# As the ad4350 vco has a minimum output of 137.5 MHz, we always
# keep it in the 200MHz to 400 MHz range, and use the
# ad9508 dividers to reduce the output  frequency further
# the statement below determines how many factors of 2 that
# we need the dividers to increase by to maintain the
# adf4350 in its operating range

if 200e6 <= adf4350_clk <= 400e6:
    lvds_reg_setting = calc_clk_cnt(adf4350_clk)
    adf4350_clk = adf4350_clk * 1
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set CNV for: 40MHz to 20MHz Range")
    my_divider.channel[2] = adf4350_clk / 10
    my_divider.channel[3] = adf4350_clk / 1
    my_adc.reg_write(0x16, lvds_reg_setting)
    my_divider.reg_write(0x2B, 0x26)

elif 100e6 <= adf4350_clk < 200e6:
    lvds_reg_setting = calc_clk_cnt(adf4350_clk)
    adf4350_clk = adf4350_clk * 2
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set CNV for: 20MHz to 10MHz Range")
    my_divider.channel[2] = adf4350_clk / 20
    my_divider.channel[3] = adf4350_clk / 2
    my_adc.reg_write(0x16, lvds_reg_setting)
    my_divider.reg_write(0x2B, 0x26)

elif 50e6 <= adf4350_clk < 100e6:
    lvds_reg_setting = calc_clk_cnt(adf4350_clk)
    adf4350_clk = adf4350_clk * 4
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set CNV for: 10MHz to 5MHz Range")
    my_divider.channel[2] = adf4350_clk / 40
    my_divider.channel[3] = adf4350_clk / 4
    my_adc.reg_write(0x16, lvds_reg_setting)
    my_divider.reg_write(0x2B, 0x16)

elif 25e6 <= adf4350_clk < 50e6:
    lvds_reg_setting = calc_clk_cnt(adf4350_clk)
    adf4350_clk = adf4350_clk * 8
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set CNV for: 5MHz to 2.5MHz Range")
    my_divider.channel[2] = adf4350_clk / 80
    my_divider.channel[3] = adf4350_clk / 8
    my_adc.reg_write(0x16, lvds_reg_setting)
    my_divider.reg_write(0x2B, 0x16)

elif 10e6 <= adf4350_clk < 25e6:
    lvds_reg_setting = calc_clk_cnt(adf4350_clk)
    adf4350_clk = adf4350_clk * 16
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set for CNV default: 2.5MHz to 1MHz Range")
    my_divider.channel[2] = adf4350_clk / 160
    my_divider.channel[3] = adf4350_clk / 16
    my_adc.reg_write(0x16, lvds_reg_setting)
    my_divider.reg_write(0x2B, 0x16)

else:
    # Default case, in event that input is out of range
    adf4350_clk = 400e6
    adf4350_clk = adf4350_clk * 1
    print(f"ADF4350 PLL Frequency set to: {adf4350_clk}")
    my_pll.frequency_altvolt0 = adf4350_clk
    print("Set CNV for: 40MHz to 20MHz Range")
    my_divider.channel[2] = adf4350_clk / 10
    my_divider.channel[3] = adf4350_clk / 1
    my_adc.reg_write(0x16, 0x51)
    my_divider.reg_write(0x2B, 0x26)
time.sleep(0.5)

print("CNV Frequency: ", my_divider.channel[2])
print("CLK Frequency: ", my_divider.channel[3])

time.sleep(0.5)
# Renable the AD9508 outputs
my_one_bit_adc_dac.gpio_sync_n = 0

time.sleep(0.25)
# Disable filter to perform LVDS interface synchronization routine
my_adc.filter_sel = "disabled"
time.sleep(0.25)
# Performs the LVDS interface synchronization routine
my_adc.lvds_sync = "enable"
time.sleep(0.25)

# Configure the Integrated Digital Filter
my_adc.filter_sel = FiltMode
time.sleep(0.25)
my_adc.sinc_dec_rate = DecRate
time.sleep(0.25)
print("ad4080 Filter Mode: ", my_adc.filter_sel)
print("ad4080 Decimation: ", my_adc.sinc_dec_rate)
print("ad4080 sampling frequency: ", my_adc.sampling_frequency)
# Need to set delay longer for decimated results
total_data_acquire_time = my_acq_size * (1 / my_adc.sampling_frequency)
print("Total Data Acquire Time: ", total_data_acquire_time)
set_timeout = int((total_data_acquire_time * 10000) + 2000)
print("Set Timeout Value (ms): ", set_timeout / 10)
my_adc._ctx.set_timeout(set_timeout)  # Timeout setting

# Acquire ADC conversion results
data = my_adc.rx()
my_adc.filter_sel = "disabled"

# ADC parameters
adc_freq = my_adc.sampling_frequency
adc_buff_n = my_acq_size
adc_bits = 20
adc_quants = 2 ** adc_bits
adc_vref = 3
adc_quant_v = adc_vref / adc_quants
test_type = "sig_input"  # 'sig_input' 'dyn_range'
# test_type = 'dyn_range'

# Analyze spectrum and show plots
# spectrum.analyze(test_type, data, adc_bits, adc_vref, adc_freq, window='blackman')

(snr_adj, thd_calc, f1_freq, fund_dbfs) = process_adc_raw_data(
    my_adc, 1, data, my_acq_size, adc_freq, 1
)

# Teardown, not sure if entirely necessary, but had seen some setup errors on starting up without this
del my_pll
del my_one_bit_adc_dac
del my_divider
del my_adc
