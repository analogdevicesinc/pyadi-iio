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
talise_ip = "192.168.1.1"
talise_uri = "ip:" + talise_ip

dev = adi.adar1000_array(
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
print("ADAR1000 array object created.")

##############################################
## Step 2: Configure TR Source & PA Bias ##
##############################################
for device in dev.devices.values():
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

tries = 10
for device in dev.devices.values():
    for channel in device.channels:
        channel.pa_bias_on = -4.8
        if round(channel.pa_bias_on, 1) != -4.8:
            for _ in range(tries):
                if round(channel.pa_bias_on, 1) == -4.8:
                    break
            else:
                print(f"Not set properly: {channel.pa_bias_on=}  Element: {channel}")

        channel.pa_bias_off = -4.8
        if round(channel.pa_bias_off, 1) != -4.8:
            for _ in range(tries):
                if round(channel.pa_bias_off, 1) == -4.8:
                    break
            else:
                print(f"Not set properly: {channel.pa_bias_off=}  Element: {channel}")
    dev.latch_tx_settings()

dev.latch_tx_settings()
print("PA bias configured.")

mr.disable_pa_bias_channel(dev)

##############################################
## Step 3: Load Saved Cal Values (if available) ##
##############################################
cal_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tx_cal_values.json")

phase_dict = {}
gain_dict = {}
atten_dict = {}

if os.path.exists(cal_json_path):
    with open(cal_json_path, "r") as f:
        cal_data = json.load(f)

    phase_dict = {int(k): v for k, v in cal_data["phase_dict"].items()}
    gain_dict  = {int(k): v for k, v in cal_data["gain_dict"].items()}
    atten_dict = {int(k): v for k, v in cal_data["atten_dict"].items()}

    # Apply cal values to hardware
    for element in dev.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.tx_phase = phase_dict.get(value, 0)
        element.tx_gain = gain_dict.get(value, 127)
        element.tx_attenuator = atten_dict.get(value, 1)
    dev.latch_tx_settings()
    print(f"Loaded and applied cal values from: {cal_json_path}")
    print(f"  phase_dict: {len(phase_dict)} elements")
    print(f"  gain_dict:  {len(gain_dict)} elements")
    print(f"  atten_dict: {len(atten_dict)} elements")
else:
    print(f"No cal file found at {cal_json_path} — using defaults (gain=127, phase=0, atten=1).")
    for element in dev.elements.values():
        element.tx_attenuator = 1
        element.tx_gain = 127
        element.tx_phase = 0
    dev.latch_tx_settings()

##############################################
## Step 4: Array Shape Definitions ##
##############################################
array_shapes = {
    "4x4":       [19, 27, 20, 28, 21, 29, 22, 30, 35, 43, 36, 44, 37, 45, 38, 46],
    "6x6":       [19, 27, 20, 28, 21, 29, 22, 30, 35, 43, 36, 44, 37, 45, 38, 46,
                  10, 18, 26, 34, 42, 50, 51, 52, 53, 54, 55, 47, 39, 31, 23, 15, 14, 13, 12, 11],
    "8x8":       list(range(1, 65)),
    "outer":     [1, 2, 3, 4, 5, 6, 7, 8, 9, 17, 25, 33, 41, 49, 57, 58, 59, 60, 61, 62, 63, 64, 56, 48, 40, 32, 24, 16],
    "subarray 1": [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],
    "subarray 2": [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],
    "subarray 3": [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],
    "subarray 4": [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],
    "single":    [37],
}

subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],
])

active_array = np.array(array_shapes["8x8"])

print("\n=== ADSY2301 Init Complete ===")
print("Available objects: dev, mr, phase_dict, gain_dict, atten_dict, array_shapes, subarray, active_array")
print("Set a breakpoint below or use the debug console to interact with the hardware.\n")


for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"
# --- Set breakpoint here to start debugging ---
pass
