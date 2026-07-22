# ==========================================================================
# ADSY2301 — Hardware Initialization (Standalone / Debug)
# --------------------------------------------------------------------------
# Initialises the ADAR1000 array, configures PA bias voltages, and loads
# saved TX calibration values (phase, gain, attenuation) from a JSON file.
#
# This script is intended for interactive use — run it, then inspect or
# modify `dev`, `mr`, `phase_dict`, `gain_dict`, `atten_dict`, etc. in
# your debugger console.
#
# No external instruments (Millibox, power supply, spectrum analyser) are
# required.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
import adi
import numpy as np
import json
import os
import ADSY2301 as mr
from adi import adar1000


##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
talise_ip = "10.75.161.150"
# talise_ip = "192.168.1.1"
talise_uri = "ip:" + talise_ip

dev = adi.adar1000_array(
    uri=talise_uri,

    chip_ids=[
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", 
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", 
    ],

    device_map=[[1, 3, 2, 4]],

    element_map=np.array([
        [1,  5,  9, 13 ],
        [2,  6, 10, 14 ],
        [3,  7, 11, 15 ],
        [4,  8, 12, 16 ],

    ]),

    device_element_map={
        1:  [5, 6, 2, 1],     3:  [13, 14, 10, 9],
        2:  [4, 4, 7, 16],  4:  [12, 11, 15, 16],
    },
)
print("ADAR1000 array object created.")

for device in dev.devices.values():
    device.tr_source = "spi"
    device.mode = "rx"
    device.bias_dac_mode = "on"

mr.disable_pa_bias_channel(dev)

print("Setting all devices to rx mode")
for element in dev.elements.values():
    element.tx_attenuator = 1
    element.tx_gain = 127# 127: Highest gain; 0: Lowest gain
    element.tx_phase = 0

dev.latch_tx_settings()

for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"

dev.latch_tx_settings()
mr.enable_pa_bias_channel(dev,[1])

dev.latch_tx_settings()
