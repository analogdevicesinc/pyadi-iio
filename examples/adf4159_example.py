# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import time

import adi

# create pll instance
pll = adi.adf4159()

# Configure pll attributes
pll.frequency = 5900000000  # Output frequency divided by 2. As O/p range of pll is 10.6 to 13 GHz this value can be 5.3GHz to 6.5GHz
pll.enable = 0  # Power down mode
pll.freq_dev_range = 0  # frequency deviation range
pll.freq_dev_step = 5690  # frequency deviation step
pll.freq_dev_time = 0  # frequency deviation time

# probe vtune and check if the values change after each 5 seconds
while True:
    pll.ramp_mode = "disabled"
    print("disabled")
    time.sleep(5)
    pll.ramp_mode = "continuous_sawtooth"
    print("continuous_sawtooth")
    time.sleep(5)
    pll.ramp_mode = "continuous_triangular"
    print("continuous_triangular")
    time.sleep(5)
    pll.ramp_mode = "single_sawtooth_burst"
    print("single_sawtooth_burst")
    time.sleep(5)
    pll.ramp_mode = "single_ramp_burst"
    print("single_ramp_burst")
    time.sleep(5)
    print("Done")
