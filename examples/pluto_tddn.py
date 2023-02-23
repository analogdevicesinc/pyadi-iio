# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi

sdr = adi.Pluto()

# Enable phaser logic in pluto
gpio = adi.one_bit_adc_dac("ip:192.168.2.1")
time.sleep(0.5)
gpio.gpio_phaser_enable = True
time.sleep(0.5)

# Configure TDD properties
tdd = adi.tddn("ip:pluto.local")
tdd.enable = False  # make sure the TDD is disabled before changing properties
tdd.frame_length_ms = 4  # each GPIO toggle is spaced 4ms apart
tdd.startup_delay_ms = 0  # do not set a startup delay
tdd.burst_count = 3  # there is a burst of 3 toggles, then off for a long time
tdd.channel[0].on_ms = 0.5  # the first trigger will happen 0.5ms into the buffer
tdd.channel[0].off_ms = 0.6  # each GPIO pulse will be 100us (0.6ms - 0.5ms)
tdd.channel[0].enable = True  # enable CH0 output
tdd.sync_external = True  # enable external sync trigger
tdd.enable = True  # enable TDD engine
