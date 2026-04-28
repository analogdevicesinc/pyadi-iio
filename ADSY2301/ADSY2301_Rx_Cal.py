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
os.environ['QT_QPA_PLATFORM'] = 'wayland'
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
import paramiko
import ADSY2301 as mr
 
 
 
# ==========================================================================
# STEP 0 — SSH Connection & Hardware Initialization
# ==========================================================================
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
 
SELF_BIASED_LNAs = True
ARRAY_MODE = "rx"
url = "ip:192.168.1.1"
print("Connecting to", url ,"...")
 
# ==========================================================================
# STEP 1 — Configure ADRV9009 Transceiver
# ==========================================================================
tddn = adi.tddn(uri = url)
fs_RxIQ = 245.76e6  # RX IQ sample rate (Hz)
conv = adi.adrv9009_zu11eg(uri = url)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12  # 4096 samples per capture
conv.dds_phases = []
 
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
sray = adi.adar1000_array(
    uri = url,
   
    chip_ids = ["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
 
                "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
                "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
 
   
    device_map = [[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
 
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
 
# Phase search range for calibration (1-degree resolution over full circle)
delay_phases = np.arange(-180,181,1)

# Disable all channels before configuring
mr.disable_stingray_channel(sray)
sray.latch_rx_settings()
 
# Identify non-reference elements (these are the ones we calibrate against the reference)
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0],-1))
 
# Set all elements to RX mode with max gain and zero phase offset
if ARRAY_MODE == "rx":
    print("ARRAY_MODE =",ARRAY_MODE,"Setting all devices to rx mode")
    for element in sray.elements.values():
        element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
        element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
        element.rx_phase = 0 # Set all phases to 0
    sray.latch_rx_settings()
 
# Point beam at boresight
sray.steer_rx(azimuth=0, elevation=0)
 
# Configure ADXUD1AEBZ PLL and gain mode
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"
 
# ==========================================================================
# STEP 4 — Calibration (Gain + Phase)
# ==========================================================================
 
input("Make sure RF is on! Press Enter to continue...")
 
# Enable subarray reference
mr.enable_stingray_channel(sray,subarray)
 
# Pre-calibration data capture
no_cal_data = np.transpose(np.array(mr.data_capture(conv)))
 
# --- Gain calibration ---
mr.disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(sray, conv, subarray, adc_map, sray.element_map)
 
# --- Phase calibration ---
print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)
 
# Post-calibration data capture
mr.enable_stingray_channel(sray)
calibrated_data = np.transpose(np.array(mr.data_capture(conv)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = mr.cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
mr.disable_stingray_channel(sray)
 
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