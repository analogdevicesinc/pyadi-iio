# ==========================================================================
# ADSY2301 — 64-Element RX Array Calibration & Sweep
# --------------------------------------------------------------------------
# This script calibrates the ADSY2301 phased-array receive path
# (gain equalization + per-element phase alignment) and plots
# before/after IQ data to verify the calibration quality.
#
# PREREQUISITES
#   1. Run ADSY2301_bootstrap_tiles.py (or the equivalent shell commands
#      on the SoM) to initialize the ADAR1000 tiles.
#   2. Ensure an RF source is active at the array’s operating frequency.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import os
import adi 
from adi import adsy2301 as mr
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
import paramiko
import subprocess
import sys

ip_address = "10.75.161.151"
uri = "ip:" + ip_address
  
dev = mr.adsy2301(uri=uri)
dev.init_BFC(

    chip_ids=[
        "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", "adar1000_csb_1_2_1", "adar1000_csb_1_2_4",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_2",
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", "adar1000_csb_0_2_1", "adar1000_csb_0_2_4",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2",
    ],

    device_map=[[6, 1, 8, 3], [5, 2, 7, 4], [14, 9, 16, 11], [13, 10, 15, 12]],

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
        1:  [25, 26, 18, 17],  3:  [57, 58, 50, 49],
        2:  [20, 19, 27, 28],  4:  [52, 51, 59, 60],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [9, 10, 2, 1],     8:  [41, 42, 34, 33],
        9:  [29, 30, 22, 21],  11: [61, 62, 54, 53],
        10: [24, 23, 31, 32],  12: [56, 55, 63, 64],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [13, 14, 6, 5],    16: [45, 46, 38, 37],
    },
)
dev.init_UDC()
dev.init_ADRV9009()
dev.udc.RX_UDC_Band_0()
dev.udc.adrf5030.RX_SW_Enable()
dev.udc.admv8913.set_filter_widest()
dev.udc.adf4382.altvolt0_frequency = int(15e9)
dev.udc.adf4382.altvolt1_frequency = int(15e9)
 
# ==========================================================================
# STEP 1 — Configure ADRV9009 Transceiver
# ==========================================================================
mr.sdr_init(dev)
mr.tdd_init(dev,TXRX_Bit=0)
 
# ==========================================================================
# STEP 2 — Define Subarrays, Reference Channels, and ADC Maps
# ==========================================================================
# The 64 elements are divided into 4 subarrays of 16 elements each.
# Each subarray feeds one ADC channel on the transceiver.
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 4
    ])
subarray_ref = np.array([1, 33, 37, 5])   # One reference element per subarray
adc_map      = np.array([0, 1, 2, 3])      # ADC channel index for each subarray
adc_ref      = 0                            # ADC channel used as the phase reference
 
# ==========================================================================
# STEP 3 — Initialize ADAR1000 Array
# ==========================================================================

# Phase search range for calibration (1-degree resolution over full circle)
delay_phases = np.arange(-180,181,1)

# Disable all channels before configuring
mr.disable_rx_channel(dev.BFC)
dev.BFC.latch_rx_settings()
 
# Identify non-reference elements (these are the ones we calibrate against the reference)
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0],-1))
 
# Set all elements to RX mode with max gain and zero phase offset
for element in dev.BFC.elements.values():
    element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
    element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
    element.rx_phase = 0 # Set all phases to 0
dev.BFC.latch_rx_settings()
 
# Point array at boresight
dev.BFC.steer_rx(azimuth=0, elevation=0)
 
cal_ant = mr.find_phase_delay_fixed_ref(dev.BFC, dev.ADRV9009, subarray_ref, adc_ref, delay_phases)

# =========================================================================
# STEP 4 — Calibration (Gain + Phase)
# ==========================================================================
 
input("Make sure RF is on! Press Enter to continue...")
 
# Enable subarray reference
mr.enable_rx_channel(dev.BFC,subarray)
 
# Pre-calibration data capture
no_cal_data = np.transpose(np.array(mr.data_capture(dev.ADRV9009)))
 
# --- Gain calibration ---
mr.disable_rx_channel(dev.BFC)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(dev.BFC, dev.ADRV9009, subarray, adc_map, dev.BFC.element_map)
 
# --- Phase calibration ---
print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(dev.BFC, dev.ADRV9009, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(dev.BFC, dev.ADRV9009, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)
 
# Post-calibration data capture
mr.enable_rx_channel(dev.BFC)
calibrated_data = np.transpose(np.array(mr.data_capture(dev.ADRV9009)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = mr.cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
mr.disable_rx_channel(dev.BFC)
 
# ==========================================================================
# STEP 5 — Plot Results
# ==========================================================================
fig, axs = plt.subplots(2,1)
 
axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100,600])
axs[0].set_ylim([-28000,28000])
 
axs[1].plot(calibrated_data.real)
axs[1].set_title('With Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_ylim([-28000,28000])
axs[1].set_xlim([100,600])
 
plt.tight_layout()
plt.savefig('ADSY2301_64Element_Electronic_Steering_Array_Calibration.png')
print("Saved plot to ADSY2301_64Element_Electronic_Steering_Array_Calibration.png")
plt.show()
input("Press Enter to exit...")