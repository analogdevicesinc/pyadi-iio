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
from adi import adsy2301 as mr
import numpy as np
import json
import os

talise_ip = "10.75.161.151"
talise_uri = "ip:" + talise_ip

dev = mr.adsy2301(uri=talise_uri)

dev.init_BFC(
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


dev.initialize_devices(pa_off=-4.8,pa_on=-4.8,lna_off=-4.8,lna_on=-4.8)

for device in dev.BFC.devices.values():
    device.mode = "rx"
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

mr.disable_rx_channel(dev.BFC)
mr.disable_tx_channel(dev.BFC)

print("Setting all devices to rx mode")
for element in dev.BFC.elements.values():
    element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
    element.tx_attenuator = 0
    element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
    element.tx_gain = 0 #Lowest gain
    element.rx_phase = 0 # Set all phases to 0
    element.tx_phase = 0

dev.BFC.latch_rx_settings()
dev.BFC.latch_tx_settings()