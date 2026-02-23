# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg') # or 'Qt5Agg', 'QtAgg'
import numpy as np
from scipy import signal
import fft_analysis
from collections import namedtuple

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))

# Individual device access (for first plot demonstration)
hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")
ad5696_dev     = adi.ad5686(uri=my_uri)
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")

tddn = adi.tddn(my_uri)
tddn.burst_count = 0
tddn.startup_delay_ms = 0
tddn.frame_length_raw  = 20

tddn.enable = 0

tddn.channel[0].on_raw   = 0
tddn.channel[0].off_raw  = 10
tddn.channel[0].polarity = 0
tddn.channel[0].enable   = 1

tddn.channel[1].on_raw   = 0
tddn.channel[1].off_raw  = 10
tddn.channel[1].polarity = 0
tddn.channel[1].enable   = 1

tddn.enable = 1

gpio_controller.gpio_clk_sel = 0

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

custom_pattern       = 0x7fff
fixed_test_pattern   = 0x10
ramp_pattern         = 0x40
pattern_disabled     = 0x00

hmcad15xx_dev1.rx_buffer_size = 2**16
hmcad15xx_dev2.rx_buffer_size = 2**16

hmcad15xx_dev1.rx_enabled_channels = [0]
hmcad15xx_dev2.rx_enabled_channels = [0]

print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))

hmcad15xx_dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev1.hmcad15xx_register_write(0x25, ramp_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x25, ramp_pattern)

#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3

hmcad15xx_dev1.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[1].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[2].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[3].input_select = "IP1_IN1"

hmcad15xx_dev2.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[1].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[2].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[3].input_select = "IP1_IN1"

# First demonstration: Individual device capture (non-synchronized)
capture_data1  = hmcad15xx_dev1.rx()
capture_data2  = hmcad15xx_dev2.rx()

# Plot channel 0 from both devices (individual capture)
plt.figure(figsize=(12, 6))
plt.plot(capture_data1, label='hmcad15xx_dev1 - Channel 0', alpha=0.7)
plt.plot(capture_data2, label='hmcad15xx_dev2 - Channel 0', alpha=0.7)
plt.xlabel('Sample Index')
plt.ylabel('ADC Value')
plt.title('ADC Data - Channel 0 from Both Devices (Individual Capture)')
plt.legend()
plt.grid(True)
plt.savefig("Data channels 0 of both devices - Individual")
plt.close()  # Close the figure to free memory

# Second demonstration: Synchronized multi-ADC capture using sharkbyte class
print("\n--- Synchronized Multi-ADC Capture ---")
multi = adi.sharkbyte(uri=my_uri,
                      device1_name="axi_adc1_hmcad15xx",
                      device2_name="axi_adc2_hmcad15xx",
                      tddn=tddn)

# Configure buffer size and enabled channels
multi.rx_buffer_size = 2**16
multi.rx_enabled_channels = [0]  # Apply to both devices

print("Multi-ADC rx_enabled_channels: " + str(multi.rx_enabled_channels))

# Configure individual device settings via dev1 and dev2 properties
multi.dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
multi.dev1.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev2.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev1.hmcad15xx_register_write(0x25, pattern_disabled)
multi.dev2.hmcad15xx_register_write(0x25, pattern_disabled)

# Set input selections
multi.dev1.channel[0].input_select = "IP4_IN4"
multi.dev2.channel[0].input_select = "IP4_IN4"
multi.dev1.channel[1].input_select = "IP4_IN4"
multi.dev2.channel[1].input_select = "IP4_IN4"
multi.dev1.channel[2].input_select = "IP4_IN4"
multi.dev2.channel[2].input_select = "IP4_IN4"
multi.dev1.channel[3].input_select = "IP4_IN4"
multi.dev2.channel[3].input_select = "IP4_IN4"

# Perform synchronized capture
sync_data1, sync_data2 = multi.rx()

# Plot synchronized channel 0 from both devices
plt.figure(figsize=(12, 6))
plt.plot(sync_data1, label='hmcad15xx_dev1 - Channel 0 (Synced)', alpha=0.7)
plt.plot(sync_data2, label='hmcad15xx_dev2 - Channel 0 (Synced)', alpha=0.7)
plt.xlabel('Sample Index')
plt.ylabel('ADC Value')
plt.title('ADC Data - Channel 0 from Both Devices (TDD Synchronized)')
plt.legend()
plt.grid(True)
plt.savefig("Data channels 0 of both devices - Synchronized")
plt.close()  # Close the figure to free memory

print("Synchronized data capture complete!")

tddn.enable = 0

tddn.channel[0].on_ms    = 0
tddn.channel[0].off_ms   = 0
tddn.channel[0].polarity = 0
tddn.channel[0].enable   = 1

tddn.channel[1].on_ms    = 0
tddn.channel[1].off_ms   = 0
tddn.channel[1].polarity = 0
tddn.channel[1].enable   = 1

tddn.enable = 1
tddn.enable = 0

# Cleanup buffers
hmcad15xx_dev1.rx_destroy_buffer()
hmcad15xx_dev2.rx_destroy_buffer()
multi.rx_destroy_buffer()