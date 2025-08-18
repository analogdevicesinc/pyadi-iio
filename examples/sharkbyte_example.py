# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from adi import sshfs
from collections import namedtuple

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.15"
print("uri: " + str(my_uri))


hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")
ssh = adi.sshfs(address=my_uri, username="root", password="analog")
ad5696_dev     = adi.ad5686(uri=my_uri)

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

base_addr_1   = 0x44A00000
base_addr_2   = 0x44A60000
mask_reg     = 0x80
scratch_reg  = 0x08

custom_pattern       = 0xa500
fixed_test_pattern   = 0x10
ramp_pattern         = 0x40
pattern_disabled     = 0x00

stdout, stderr = ssh._run(f"busybox devmem {base_addr_1+mask_reg} 32 0xef")
stdout, stderr = ssh._run(f"busybox devmem {base_addr_2+mask_reg} 32 0x10")

hmcad15xx_dev1.rx_buffer_size = 2**16
hmcad15xx_dev2.rx_buffer_size = 2**16

hmcad15xx_dev1.rx_enabled_channels = [0]
hmcad15xx_dev2.rx_enabled_channels = [0]

print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))


stdout, stderr = ssh._run(f"busybox devmem {base_addr_1+scratch_reg} 32")
print(stdout)

if stdout == "0x00000000":
    #clk_div_available value: CLK_DIV_1 CLK_DIV_2 CLK_DIV_4 CLK_DIV_8
    hmcad15xx_dev1.clk_div = "CLK_DIV_1"
    hmcad15xx_dev2.clk_div = "CLK_DIV_1"
    print("RX1 CLK_DIV is: " + hmcad15xx_dev1.clk_div)
    print("RX2 CLK_DIV is: " + hmcad15xx_dev2.clk_div)

    #operation_mode_available value: SINGLE_CHANNEL DUAL_CHANNEL QUAD_CHANNEL

    hmcad15xx_dev1.operation_mode = "SINGLE_CHANNEL"
    hmcad15xx_dev2.operation_mode = "SINGLE_CHANNEL"
    print("RX1 Operation mode is: " + hmcad15xx_dev1.operation_mode)
    print("RX2 Operation mode is: " + hmcad15xx_dev2.operation_mode)

    #input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3 IP4_IN4

    hmcad15xx_dev1.channel[0].input_select=  "IP4_IN4"
    hmcad15xx_dev1.channel[1].input_select = "IP4_IN4"
    hmcad15xx_dev1.channel[2].input_select = "IP4_IN4"
    hmcad15xx_dev1.channel[3].input_select = "IP4_IN4"

    hmcad15xx_dev2.channel[0].input_select=  "IP4_IN4"
    hmcad15xx_dev2.channel[1].input_select = "IP4_IN4"
    hmcad15xx_dev2.channel[2].input_select = "IP4_IN4"
    hmcad15xx_dev2.channel[3].input_select = "IP4_IN4"


    stdout, stderr = ssh._run(f"busybox devmem {base_addr_1+scratch_reg} 32 0xAD")
    print(stdout)

hmcad15xx_dev1.hmcad15xx_register_write(0x46, 0x0)
hmcad15xx_dev2.hmcad15xx_register_write(0x46, 0x0)

hmcad15xx_dev1.hmcad15xx_register_write(0x42, 0x40)
hmcad15xx_dev2.hmcad15xx_register_write(0x42, 0x40)

data_out          = [0] * 8

check_data = False

if check_data == True:

    print(f"Writting single custom pattern: {hex(custom_pattern)}")
    hmcad15xx_dev1.hmcad15xx_register_write(0x25, fixed_test_pattern)
    hmcad15xx_dev2.hmcad15xx_register_write(0x25, fixed_test_pattern)
    hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)
    hmcad15xx_dev2.hmcad15xx_register_write(0x26, custom_pattern)

    for i in range(200):
        data  = hmcad15xx_dev1.rx()

        data_out[0] = hex(data[0])
        data_out[1] = hex(data[1])
        data_out[2] = hex(data[2])
        data_out[3] = hex(data[3])
        data_out[4] = hex(data[4])
        data_out[5] = hex(data[5])
        data_out[6] = hex(data[6])
        data_out[7] = hex(data[7])
        if any(x != "0xa5" for x in data_out):
            print(f"Data out1: {data_out} and i: {i}")

        data1  = hmcad15xx_dev2.rx()

        data_out[0] = hex(data1[0])
        data_out[1] = hex(data1[1])
        data_out[2] = hex(data1[2])
        data_out[3] = hex(data1[3])
        data_out[4] = hex(data1[4])
        data_out[5] = hex(data1[5])
        data_out[6] = hex(data1[6])
        data_out[7] = hex(data1[7])
        if any(x != "0xa5" for x in data_out):
            print(f"Data out1: {data_out} and i: {i}")
        hmcad15xx_dev1.rx_destroy_buffer()
        hmcad15xx_dev2.rx_destroy_buffer()

hmcad15xx_dev1.hmcad15xx_register_write(0x25, pattern_disabled)
hmcad15xx_dev2.hmcad15xx_register_write(0x25, pattern_disabled)

capture_data   = hmcad15xx_dev1.rx()
capture_data1  = hmcad15xx_dev2.rx()

# plot setup

fig, axs = plt.subplots(2, 1)

# Plot ADC1 channels

axs[0].plot(capture_data)
axs[0].set_ylabel("Channel 4 amplitude ADC1")
axs[0].set_xlabel("Samples")

axs[1].plot(capture_data1)
axs[1].set_ylabel("Channel 4 amplitude ADC2")
axs[1].set_xlabel("Samples")

plt.tight_layout()
plt.show()

hmcad15xx_dev1.rx_destroy_buffer()
hmcad15xx_dev2.rx_destroy_buffer()