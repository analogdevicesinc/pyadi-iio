#Dual Stingray Mirror
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import time
import importlib
from calibration import *
import genalyzer as gn
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
# import adar_functions
import re
import json
import os
import pandas as pd

 
SELF_BIASED_LNAs = True
ARRAY_MODE = "rx" # start rx cals first
#print("Turn on RF Source...")
#input('Press Enter to continue...')
url = "ip:192.168.0.1"
print("Connecting to", url ,"...")
 
# url = "local:" if len(sys.argv) == 1 else sys.argv[1]
ssh = sshfs(address=url, username="root", password="analog")
 
 
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 4


 
    ])
subarray_ref = np.array([1, 33, 37, 5])  # subarray reference elements
# adc_map      = np.array([3, 0, 1, 2])  # ADC map to subarray
adc_map      = np.array([2, 3, 0, 1])  # ADC map to subarray
# adc_map      = np.array([0, 1, 2, 3])  # ADC map to subarray
adc_ref      = 0  # ADC reference channel (indexed at 0)


# Setup Talise RX, TDDN Engine & ADAR1000

conv = adi.adrv9009_zu11eg(uri = url)
 
conv._rxadc.set_kernel_buffers_count(2) # set buffers as 2 to avoid stale data on AD9081
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12
conv.dds_phases = []
# conv.rx_nyquist_zone     = ["even"] * 4
 
# conv.tx_main_nco_frequencies = [450000000] * 4
# conv.tx_enabled_channels = [0, 1, 2, 3]
# conv.tx_main_nco_phases = [0] * 4
# conv.tx_channel_nco_frequencies = [0] * 4
# conv.tx_cyclic_buffer = True
# conv.tx_ddr_offload = False
 
tddn = adi.tddn(uri = url)
sray = adi.adar1000_array(
    uri = url,
 
    # chip_ids = ["adar1000_csb_0_2_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
    #             "adar1000_csb_0_1_4", "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_1_1",
 
    #             "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
    #             "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

        # chip_ids = ["adar1000_csb_0_1_1", "adar1000_csb_0_1_3", "adar1000_csb_1_1_1", "adar1000_csb_1_1_2",
        #         "adar1000_csb_0_1_2", "adar1000_csb_0_1_4", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
 
        #         "adar1000_csb_0_2_1", "adar1000_csb_0_2_2", "adar1000_csb_1_2_1", "adar1000_csb_1_2_2",
        #         "adar1000_csb_0_2_3", "adar1000_csb_0_2_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

    # chip_ids = ["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_1",
    #             "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
 
    #             "adar1000_csb_0_2_2", "adar1000_csb_0_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
    #             "adar1000_csb_0_2_3", "adar1000_csb_0_2_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

    chip_ids = ["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
 
                "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
                "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

    
    device_map = [[1, 2, 5, 6], [3, 4, 7, 8], [9, 10, 13, 14], [11, 12, 15, 16]],
 
    element_map = np.array([[1, 9,  17, 25, 33, 41, 49, 57],
                            [2, 10, 18, 26, 34, 42, 50, 58],
                            [3, 11, 19, 27, 35, 43, 51, 59],
                            [4, 12, 20, 28, 36, 44, 52, 60],
                            
                            [5, 13, 21, 29, 37, 45, 53, 61],
                            [6, 14, 22, 30, 38, 46, 54, 62],
                            [7, 15, 23, 31, 39, 47, 55, 63],
                            [8, 16, 24, 32, 40, 48, 56, 64]]),
    
    device_element_map = {
 
        1:  [9, 10, 2, 1],      3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],   4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12]  ,   7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],   8:  [52, 51, 59, 60],
 
        9:  [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],   12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],     15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],   16: [56, 55, 63, 64],
    },

)
 
# Startup and connect TDDN
tddn.enable = True
tddn.startup_delay_ms = 0
# Configure top level engine
frame_length_ms = 1
tddn.frame_length_ms = frame_length_ms
# Configure component channels
off_time = frame_length_ms - 0.1
# Setup TDDN Channel for CW mode
tddn_channels = {
    "TX_OFFLOAD_SYNC": 0,
    "RX_OFFLOAD_SYNC": 1,
    "TDD_ENABLE": 2,
    "RX_MXFE_EN": 3,
    # "TX_MXFE_EN": 4,
    # "TX_STINGRAY_EN": 5
}
# Assign channel properties for CW
for key, value in tddn_channels.items():
    if value == 0 or value == 1:
        tddn.channel[value].on_raw = 0
        tddn.channel[value].off_raw = 0
        tddn.channel[value].on_ms = 0
        tddn.channel[value].off_ms = 0
        tddn.channel[value].polarity = True
        tddn.channel[value].enable = True
    elif value == 2 or value == 5:
        tddn.channel[value].on_raw = 0
        tddn.channel[value].off_raw = 0
        tddn.channel[value].on_ms = 0
        tddn.channel[value].off_ms = 0
        tddn.channel[value].polarity = False
        tddn.channel[value].enable = True
    else:
        tddn.channel[value].on_raw = 0
        tddn.channel[value].off_raw = 10
        tddn.channel[value].polarity = True
        tddn.channel[value].enable = True
tddn.enable = True # Fire up TDD engine
tddn.sync_internal = True # software enable TDD mode
# Setup Stingray for RX mode
 
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d] # analog target channels
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0],-1)) # matrix of subarray target channels to enable/disable wrt reference
 

if ARRAY_MODE == "rx":
    print("ARRAY_MODE =",ARRAY_MODE,"Setting all devices to rx mode")
    for element in sray.elements.values():
        element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
        element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
        element.rx_phase = 0 # Set all phases to 0
    sray.latch_rx_settings() # Latch SPI settings to devices


 
disable_stingray_channel(sray, elements=None, man_input=False)
 
 
# enable_stingray_channel(sray, elements=None, man_input=True)