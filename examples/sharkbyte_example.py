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
from collections import namedtuple

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))


hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")
ad5696_dev     = adi.ad5686(uri=my_uri)

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

custom_pattern       = 0x5a00
fixed_test_pattern   = 0x10
ramp_pattern         = 0x40
pattern_disabled     = 0x00

hmcad15xx_dev1.rx_buffer_size = 2**16
hmcad15xx_dev2.rx_buffer_size = 2**16

hmcad15xx_dev1.rx_enabled_channels = [0]
hmcad15xx_dev2.rx_enabled_channels = [0]

print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))

#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3 IP4_IN4

hmcad15xx_dev1.channel[0].input_select=  "IP4_IN4"
hmcad15xx_dev1.channel[1].input_select = "IP4_IN4"
hmcad15xx_dev1.channel[2].input_select = "IP4_IN4"
hmcad15xx_dev1.channel[3].input_select = "IP4_IN4"

hmcad15xx_dev2.channel[0].input_select=  "IP4_IN4"
hmcad15xx_dev2.channel[1].input_select = "IP4_IN4"
hmcad15xx_dev2.channel[2].input_select = "IP4_IN4"
hmcad15xx_dev2.channel[3].input_select = "IP4_IN4"

hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x26, custom_pattern)
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