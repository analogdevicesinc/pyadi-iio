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


my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))


hmcad15xx_dev = adi.hmcad15xx(uri=my_uri)

hmcad15xx_dev.rx_buffer_size = 8096
hmcad15xx_dev.rx_enabled_channels = [0,1,2,3]
print("RX rx_enabled_channels: " + str(hmcad15xx_dev.rx_enabled_channels))

#clk_div_available value: CLK_DIV_1 CLK_DIV_2 CLK_DIV_4 CLK_DIV_8

hmcad15xx_dev.clk_div = "CLK_DIV_4"
print("CLK_DIV is: " + hmcad15xx_dev.clk_div)

#operation_mode_available value: SINGLE_CHANNEL DUAL_CHANNEL QUAD_CHANNEL

hmcad15xx_dev.operation_mode = "QUAD_CHANNEL"
print("Operation mode is: " + hmcad15xx_dev.operation_mode)


#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3 IP4_IN4

hmcad15xx_dev.channel[0].input_select=  "IP1_IN1"
hmcad15xx_dev.channel[1].input_select = "IP2_IN2"
hmcad15xx_dev.channel[2].input_select = "IP3_IN3"
hmcad15xx_dev.channel[3].input_select = "IP4_IN4"


print("Signal input 0X3A is:", hmcad15xx_dev.hmcad15xx_register_read(0x3A))
print("Signal input 0X3B is:", hmcad15xx_dev.hmcad15xx_register_read(0x3B))

print("Writing 0xABCD to 0x26 custom pattern")
hmcad15xx_dev.hmcad15xx_register_write(0x26,0xABCD)
print("0x26 custom pattern is:", hmcad15xx_dev.hmcad15xx_register_read(0x26))

# rx data

data = hmcad15xx_dev.rx()

# plot setup

# x = np.arange(0, hmcad15xx_dev.rx_buffer_size)

fig, (ch1,ch2,ch3,ch4) = plt.subplots(4, 1)

fig.suptitle("HMCAD15XX Data")
ch1.plot(data[0])
ch1.set_ylabel("Channel 1 amplitude")
ch1.set_xlabel("Samples")

ch2 = plt.subplot(4, 1, 2)
ch2.plot(data[1])
ch2.set_ylabel("Channel 2 amplitude")
ch2.set_xlabel("Samples")

ch3 = plt.subplot(4, 1, 3)
ch3.plot(data[2])
ch3.set_ylabel("Channel 3 amplitude")
ch3.set_xlabel("Samples")

ch4 = plt.subplot(4, 1, 4)
ch4.plot(data[3])
ch4.set_ylabel("Channel 4 amplitude")
ch4.set_xlabel("Samples")
plt.show()

hmcad15xx_dev.rx_destroy_buffer()