# Manta Ray 64 Element RX Electronic Steering Array Beam Pattern Test
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Use offscreen backend to avoid X11/Wayland issues
import time
import importlib
import adi
from adi.sshfs import sshfs
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime
# import adar_functions
import re
import json
import os
import pandas as pd
import mbx_functions as mbx
from scipy.special import factorial
from scipy.io import savemat
import sys
sys.path.insert(0, '/home/snuc/pyadi-iio/MantaRayTx_Cal')
import MantaRay as mr
import paramiko
import pyvisa
from N6705B_Driver import N6705B

##############################################
## Step 0: Initialize System ##
###############################################

BAUDRATE                    = 57600                    
DEVICENAME                  = "/dev/ttyUSB0"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

# Set up VISA for external instruments (for future use)
rm = pyvisa.ResourceManager()

# Keysight N6705B Power Supply (modular) for Manta Ray Rails
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B(rm, N67)

##############################################
## Step 1: Initialize RX Array ##
###############################################
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

print(f"Connecting to {talise_uri}...")

# Setup SSH connection
ssh_fs = sshfs(address="ip:192.168.1.1", username="root", password="analog")

# Setup Talise RX and ADAR1000
fs_RxIQ = 245.76e6  # I/Q Data Rate in MSPS
conv = adi.adrv9009_zu11eg(uri=talise_uri)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12

##############################################
## Step 2: Initialize ADAR1000 Array ##
###############################################

# Define RX subarrays (64 elements / 4 subarrays = 16 elements each)
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],      # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64], # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],     # subarray 4
])
subarray_ref = np.array([1, 33, 37, 5])
adc_map = np.array([0, 1, 2, 3])
adc_ref = 0

# Setup ADAR1000 Array for RX
manta_ray = adi.adar1000_array(
    uri=talise_uri,
    
    chip_ids=["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
              "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
              "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
              "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
    
    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
    
    element_map=np.array([[1, 9,  17, 25, 33, 41, 49, 57],
                          [2, 10, 18, 26, 34, 42, 50, 58],
                          [3, 11, 19, 27, 35, 43, 51, 59],
                          [4, 12, 20, 28, 36, 44, 52, 60],
                          [5, 13, 21, 29, 37, 45, 53, 61],
                          [6, 14, 22, 30, 38, 46, 54, 62],
                          [7, 15, 23, 31, 39, 47, 55, 63],
                          [8, 16, 24, 32, 40, 48, 56, 64]]),
    
    device_element_map={
        1:  [9, 10, 2, 1],      3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],   4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],     7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],   8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],   12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],     15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],   16: [56, 55, 63, 64],
    },
)

# Configure array for RX mode
mr.disable_stingray_channel(manta_ray)
manta_ray.latch_rx_settings()

# Set RX array to max gain and 0 phase
for element in manta_ray.elements.values():
    element.rx_attenuator = 0  # 0: Attenuation off (max gain)
    element.rx_gain = 127      # 127: Highest gain
    element.rx_phase = 0       # Set all phases to 0
manta_ray.latch_rx_settings()

# Capture initial phase/gain calibration
phase_dict = {i: 0.0 for i in range(1, 65)}
gain_dict = {i: 127 for i in range(1, 65)}
for element in manta_ray.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    phase_dict[value] = element.rx_phase
    gain_dict[value] = element.rx_gain

##############################################
## Step 3: RX Array Calibration Routine ##
###############################################

print("\n" + "="*70)
print("STARTING RX ARRAY CALIBRATION")
print("="*70)

# Define delay phases for phase calibration
delay_phases = np.arange(-180, 181, 1)

# Calculate subarray target channels for phase calibration
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0], -1))

# Enable all subarrays for calibration
all_elements = subarray.flatten()
mr.enable_stingray_channel(manta_ray, all_elements.tolist())
time.sleep(1)

print("Performing Gain Calibration...")
# Gain calibration
gain_dict_cal, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(
    manta_ray, conv, subarray, adc_map, manta_ray.element_map
)

print("Performing Phase Calibration... Please wait...")
# Phase calibration - find phase delay with fixed reference
cal_ant = mr.find_phase_delay_fixed_ref(manta_ray, conv, subarray_ref, adc_ref, delay_phases)

# Analog phase calibration
analog_phase, analog_phase_dict = mr.phase_analog(
    manta_ray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant
)

print("RX Array Calibration Complete!")
print("="*70 + "\n")

# Store calibration data
mr.disable_stingray_channel(manta_ray)
manta_ray.latch_rx_settings()

##############################################
## Step 3: Initialize Gimbal and Parameters ##
###############################################

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

sig_gen_freq_GHz = 10
steering_angle = 0  # degrees
maxsweepangle = 120  # degrees
sweepstep = 1
gimbal_motor = GIMBAL_H
gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))

# Define steering angles to test
steering_angles = [0]
peak_mags_az = {angle: np.full(len(gimbal_positions), np.nan) for angle in steering_angles}

## Loop through subarrays to enable and test ##
for i in subarray:
    # Enable elements for subarray
    mr.enable_stingray_channel(manta_ray, i.tolist())
    time.sleep(1)

    for j in angles:
        mbx.move(gimbal_motor, j)
        data = np.array(mr.data_capture(conv))
        # Calculate magnitude of combined signal
        combined_data = np.sum(data, axis=0)
        peak_mags_az[steering_angle][i] = mr.get_analog_mag(combined_data)
    
    print(peak_mags_az)

a=1