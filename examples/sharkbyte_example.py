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


my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))


hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")

hmcad15xx_dev1.rx_buffer_size = 1024
hmcad15xx_dev2.rx_buffer_size = 1024
hmcad15xx_dev1.rx_enabled_channels = [0,1,2,3]
hmcad15xx_dev2.rx_enabled_channels = [0,1,2,3]
print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))

#clk_div_available value: CLK_DIV_1 CLK_DIV_2 CLK_DIV_4 CLK_DIV_8

hmcad15xx_dev1.clk_div = "CLK_DIV_4"
hmcad15xx_dev2.clk_div = "CLK_DIV_4"
print("RX1 CLK_DIV is: " + hmcad15xx_dev1.clk_div)
print("RX2 CLK_DIV is: " + hmcad15xx_dev2.clk_div)

#operation_mode_available value: SINGLE_CHANNEL DUAL_CHANNEL QUAD_CHANNEL

hmcad15xx_dev1.operation_mode = "QUAD_CHANNEL"
hmcad15xx_dev2.operation_mode = "QUAD_CHANNEL"
print("RX1 Operation mode is: " + hmcad15xx_dev1.operation_mode)
print("RX2 Operation mode is: " + hmcad15xx_dev2.operation_mode)


#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3 IP4_IN4

hmcad15xx_dev1.channel[0].input_select=  "IP1_IN1"
hmcad15xx_dev1.channel[1].input_select = "IP2_IN2"
hmcad15xx_dev1.channel[2].input_select = "IP3_IN3"
hmcad15xx_dev1.channel[3].input_select = "IP4_IN4"

hmcad15xx_dev2.channel[0].input_select=  "IP1_IN1"
hmcad15xx_dev2.channel[1].input_select = "IP2_IN2"
hmcad15xx_dev2.channel[2].input_select = "IP3_IN3"
hmcad15xx_dev2.channel[3].input_select = "IP4_IN4"

print("Signal input 0X3A is:", hmcad15xx_dev1.hmcad15xx_register_read(0x3A))
print("Signal input 0X3B is:", hmcad15xx_dev1.hmcad15xx_register_read(0x3B))

custom_pattern = 0xff00
test_pattern = 0x40
print(f"Writting single custom pattern: {hex(custom_pattern)}")
hmcad15xx_dev1.hmcad15xx_register_write(0x25, test_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x25, test_pattern)
hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)


hmcad15xx_dev1.hmcad15xx_register_write(0x42, 0x40)
hmcad15xx_dev2.hmcad15xx_register_write(0x42, 0x40)

print("0x26 custom pattern is:", hmcad15xx_dev1.hmcad15xx_register_read(0x25))

# rx data

data = hmcad15xx_dev1.rx()
data1 = hmcad15xx_dev2.rx()
# plot setup

fig, axs = plt.subplots(4, 2)

# Plot ADC1 channels

axs[0, 0].plot(data[0])
axs[0, 0].set_ylabel("Channel 1 amplitude ADC1")
axs[0, 0].set_xlabel("Samples")

axs[1, 0].plot(data[1])
axs[1, 0].set_ylabel("Channel 2 amplitude ADC1")
axs[1, 0].set_xlabel("Samples")

axs[2, 0].plot(data[2])
axs[2, 0].set_ylabel("Channel 3 amplitude ADC1")
axs[2, 0].set_xlabel("Samples")

axs[3, 0].plot(data[3])
axs[3, 0].set_ylabel("Channel 4 amplitude ADC1")
axs[3, 0].set_xlabel("Samples")

# Plot ADC2 channels
axs[0, 1].plot(data1[0])
axs[0, 1].set_ylabel("Channel 1 amplitude ADC2")
axs[0, 1].set_xlabel("Samples")

axs[1, 1].plot(data1[1])
axs[1, 1].set_ylabel("Channel 2 amplitude ADC2")
axs[1, 1].set_xlabel("Samples")

axs[2, 1].plot(data1[2])
axs[2, 1].set_ylabel("Channel 3 amplitude ADC2")
axs[2, 1].set_xlabel("Samples")

axs[3, 1].plot(data1[3])
axs[3, 1].set_ylabel("Channel 4 amplitude ADC2")
axs[3, 1].set_xlabel("Samples")

plt.tight_layout()
plt.show()

hmcad15xx_dev1.rx_destroy_buffer()
hmcad15xx_dev2.rx_destroy_buffer()