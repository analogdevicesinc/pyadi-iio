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

# Sampling rate per (n_channels, bits) — matches the 6 DTS configurations
FS_MAP = {
    (4, 12): 160e6,
    (4, 8):  250e6,
    (2, 12): 320e6,
    (2, 8):  500e6,
    (1, 12): 640e6,
    (1, 8):  1000e6,
    (4, 14): 105e6,
}

hmcad15xx_dev = adi.hmcad15xx(uri=my_uri, device_name="axi_adc_hmcad15xx")
ssh = adi.sshfs(address=my_uri, username="root", password="analog")

#clk_div_available value: CLK_DIV_1 CLK_DIV_2 CLK_DIV_4 CLK_DIV_8

# hmcad15xx_dev.clk_div = "CLK_DIV_4"
# print("CLK_DIV is: " + hmcad15xx_dev.clk_div)

#operation_mode_available value: SINGLE_CHANNEL DUAL_CHANNEL QUAD_CHANNEL

# hmcad15xx_dev.operation_mode = "QUAD_CHANNEL"
# print("Operation mode is: " + hmcad15xx_dev.operation_mode)

# Auto-detect config from hardware registers written at probe time:
#   reg 0x31 (OPERATION_MODE): D[2:0] = 1/2/4 -> n_channels (8/12-bit)
#                               D[3] = precision_mode (14-bit)
#   reg 0x53 (LVDS_OUTPUT_MODE): 0x0=8bit, 0x1=12bit, 0x4=14bit (dual 8-bit LVDS)
reg31 = int(str(hmcad15xx_dev.hmcad15xx_register_read(0x31)).strip(), 0)
reg53 = int(str(hmcad15xx_dev.hmcad15xx_register_read(0x53)).strip(), 0)

lvds_mode = reg53 & 0x7
if lvds_mode == 0x4 and (reg31 & 0x8):  # 14-bit precision mode: DUAL_8BIT LVDS + precision bit D[3]
    bits = 14
    n_channels = 4
elif lvds_mode == 0x1:                   # 12-bit mode
    bits = 12
    n_channels = reg31 & 0x7
else:                                    # 8-bit mode
    bits = 8
    n_channels = reg31 & 0x7

fs = FS_MAP[(n_channels, bits)]
print(f"Detected: {n_channels} channel(s), {bits}-bit, {fs/1e6:.0f} MSPS")

hmcad15xx_dev.rx_buffer_size = 1024
hmcad15xx_dev.rx_enabled_channels = list(range(n_channels))
print("RX rx_enabled_channels: " + str(hmcad15xx_dev.rx_enabled_channels))

#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3 IP4_IN4

# hmcad15xx_dev.channel[0].input_select=  "IP1_IN1"
# hmcad15xx_dev.channel[1].input_select = "IP2_IN2"
# hmcad15xx_dev.channel[2].input_select = "IP3_IN3"
# hmcad15xx_dev.channel[3].input_select = "IP4_IN4"

# Set all 4 ADC input selects to IN1 (driver probe defaults to IN4)
for ch in range(4):
    hmcad15xx_dev.channel[ch].input_select = "IP4_IN4"

print("Signal input 0X3A is:", hmcad15xx_dev.hmcad15xx_register_read(0x3A))
print("Signal input 0X3B is:", hmcad15xx_dev.hmcad15xx_register_read(0x3B))

# test_pattern = 0x10
# custom_pattern = 0xAC5D
# hmcad15xx_dev.hmcad15xx_register_write(0x25, test_pattern)
# hmcad15xx_dev.hmcad15xx_register_write(0x26, custom_pattern)
# hmcad15xx_dev.hmcad15xx_register_write(0x46, 0x4)
# hmcad15xx_dev.hmcad15xx_register_write(0x42, 0x40)
# specify the custom value

hmcad15xx_dev.hmcad15xx_register_write(0x25, 0x00)  # normal mode
hmcad15xx_dev.hmcad15xx_register_write(0x46, 0x4)   # twos complement output
hmcad15xx_dev.hmcad15xx_register_write(0x42, 0x40)  # phase DDR

base_addr_1 = 0x44A00800
lane = 0
value = 1
stdout, stderr = ssh._run(f"busybox devmem {base_addr_1 + 4*lane} {value}")
print(stdout)

# rx data
data = hmcad15xx_dev.rx()

# plot setup

# x = np.arange(0, hmcad15xx_dev.rx_buffer_size)

# fig, (ch1,ch2,ch3,ch4) = plt.subplots(4, 1)

# fig.suptitle("HMCAD15XX Data")
# ch1.plot(data[0])
# ch1.set_ylabel("Channel 1 amplitude")
# ch1.set_xlabel("Samples")

# ch2 = plt.subplot(4, 1, 2)
# ch2.plot(data[1])
# ch2.set_ylabel("Channel 2 amplitude")
# ch2.set_xlabel("Samples")

# ch3 = plt.subplot(4, 1, 3)
# ch3.plot(data[2])
# ch3.set_ylabel("Channel 3 amplitude")
# ch3.set_xlabel("Samples")

# ch4 = plt.subplot(4, 1, 4)
# ch4.plot(data[3])
# ch4.set_ylabel("Channel 4 amplitude")
# ch4.set_xlabel("Samples")
# plt.show()

# Plot: single channel -> data este 1D array; N canale -> lista de N array-uri
if n_channels == 1:
    plt.figure()
    plt.plot(data)
    plt.title(f"Channel 1 — {bits}-bit, {fs/1e6:.0f} MSPS")
    plt.ylabel("Amplitude")
    plt.xlabel("Samples")
    plt.tight_layout()
    plt.show()
else:
    fig, axes = plt.subplots(n_channels, 1, figsize=(10, 2 * n_channels))
    for i in range(n_channels):
        axes[i].plot(data[i])
        axes[i].set_title(f"Channel {i+1} — {bits}-bit, {fs/1e6:.0f} MSPS")
        axes[i].set_ylabel("Amplitude")
    axes[-1].set_xlabel("Samples")
    plt.tight_layout()
    plt.show()

hmcad15xx_dev.rx_destroy_buffer()
