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
import sys
from pathlib import Path

# Make the local ADSY2301 helper module importable when this script is run
# from the repository root or the ADSY2301 directory.
# if str(Path(__file__).resolve().parent) not in sys.path:
#     sys.path.insert(0, str(Path(__file__).resolve().parent))

import ADSY2301 as mr

##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
talise_ip = "10.75.161.108"
talise_uri = "ip:" + talise_ip


dev = adi.adar1000_array(
    uri=talise_uri,

    chip_ids=[
        "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", 
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", 
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

for device in dev.devices.values():
    device.mode = "rx"
    device.tr_source = "spi"
    device.bias_dac_mode = "on"
    # device.lna_bias_on = -0.9412 #On bias for LNA
    device.lna_bias_on = -4.7 #pinchoff


#enable all RX channels
mr.enable_stingray_channel(dev)

mr.disable_stingray_channel(dev)