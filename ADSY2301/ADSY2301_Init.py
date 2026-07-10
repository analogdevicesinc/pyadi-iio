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

##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
talise_ip = "10.75.161.99"
talise_uri = "ip:" + talise_ip
MANUAL = False

dev_old = adi.adar1000_array(
    uri=talise_uri,

    chip_ids=[
        "adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
        "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4",
    ],

    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],

    element_map=np.array([
        [1,  9,  17, 25, 33, 41, 49, 57],
        [2,  10, 18, 26, 34, 42, 50, 58],
        [3,  11, 19, 27, 35, 43, 51, 59],
        [4,  12, 20, 28, 36, 44, 52, 60],
        [5,  13, 21, 29, 37, 45, 53, 61],
        [6,  14, 22, 30, 38, 46, 54, 62],
        [7,  15, 23, 31, 39, 47, 55, 63],
        [8,  16, 24, 32, 40, 48, 56, 64],
    ]),

    device_element_map={
        1:  [9, 10, 2, 1],     3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],  4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],  8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],    11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],  12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],  16: [56, 55, 63, 64],
    },
)

dev = adi.adar1000_array(
    uri=talise_uri,

    chip_ids=[
        "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4",
        "adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
    ],

    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],

    element_map=np.array([
        [1,  9,  17, 25, 33, 41, 49, 57],
        [2,  10, 18, 26, 34, 42, 50, 58],
        [3,  11, 19, 27, 35, 43, 51, 59],
        [4,  12, 20, 28, 36, 44, 52, 60],
        [5,  13, 21, 29, 37, 45, 53, 61],
        [6,  14, 22, 30, 38, 46, 54, 62],
        [7,  15, 23, 31, 39, 47, 55, 63],
        [8,  16, 24, 32, 40, 48, 56, 64],
    ]),

    device_element_map={
        1:  [9, 10, 2, 1],     3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],  4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],  8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],    11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],  12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],  16: [56, 55, 63, 64],
    },
)
print("ADAR1000 array object created.")
##############################################
## Step 2: Configure TR Source & PA Bias ##
##############################################
    
dev.initialize_devices(pa_off=-4.8,pa_on=-4.8,lna_off=-4.8,lna_on=-4.8)

for device in dev.devices.values():
    device.mode = "rx"
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

mr.disable_pa_bias_channel(dev)

print("Setting all devices to rx mode")
for element in dev.elements.values():
    element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
    element.tx_attenuator = 0
    element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
    element.tx_gain = 0 #Lowest gain
    element.rx_phase = 0 # Set all phases to 0
    element.tx_phase = 0
dev.latch_rx_settings()
dev.latch_tx_settings()


# for device in dev.devices.values():
#     device.tr_source = "external"
#     device.bias_dac_mode = "toggle"


