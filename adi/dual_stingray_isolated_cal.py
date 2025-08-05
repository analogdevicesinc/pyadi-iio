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
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 4
 
    ])
subarray_ref = np.array([4, 8, 40, 36])  # subarray reference elements
adc_map      = np.array([3, 0, 1, 2])  # ADC map to subarray # ADC map to subarray (not necessary in Python implementation)
adc_ref      = 3  # ADC reference channel (indexed at 0)

 
# Setup AD9081 RX, TDDN Engine & ADAR1000
# Setup Talise RX, TDDN Engine & ADAR1000
# conv = adi.ad9081(uri = url)
conv = adi.adrv9009_zu11eg(uri = url)
 
conv._rxadc.set_kernel_buffers_count(1) # set buffers as 1 to avoid stale data on AD9081
conv.rx_main_nco_frequencies = [200000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12
# conv.rx_nyquist_zone     = ["even"] * 4
 

sray = adi.adar1000_array(
    uri = url,
 
    chip_ids = ["adar1000_csb_0_2_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_4", "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_1_1",
 
                "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
                "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

    
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
 
        1:  [9, 1, 2, 10],      3:  [25, 17, 18, 26],
        2:  [11, 3, 4, 12],     4:  [27, 19, 20, 28],
        5:  [41, 33, 34, 42],   7:  [57, 49, 50, 58],
        6:  [43, 35, 36, 44],   8:  [59, 51, 52, 60],
 
        9:  [6, 14, 13, 5],     11: [22, 30, 29, 21],
        10: [8, 16, 15, 7],     12: [24, 32, 31, 23],
        13: [38, 46, 45, 37],   15: [54, 62, 61, 53],
        14: [40, 48, 47, 39],   16: [56, 64, 63, 55],
    },
)
 
for element in sray.elements.values():
    element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
    element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
    element.rx_phase = 0 # Set all phases to 0
sray.latch_rx_settings() # Latch SPI settings to devices

#########################################################################
#########################################################################
#### Initilization complete; execute functions for calibration below ####
#########################################################################
#########################################################################
f_carrier = 10.38e9 # freq of RF source
c = 299792458   # speed of light in m/s
 
''' Set distance between Rx antennas '''
d_wavelength = 0.5                # distance between elements as a fraction of wavelength.  This is normally 0.5
wavelength = c/f_carrier              # wavelength of the RF carrier
d = d_wavelength*wavelength         # distance between elements in meters
time_max = (d / c) * 1e12  # max time (in ps) needed to steer from 0 to 90 deg
 
delay_times = np.arange(-time_max, time_max, time_max/200)    # time delay in ps
delay_phases = np.arange(-180,181,1) # sweep phase from -180 to 180 in 1 degree steps.
 
#### Plot data with no calibration ####
fig, axs = plt.subplots(2,1) # Creates a 3x1 grid of subplots
 
enable_stingray_channel(sray, subarray_ref)
no_cal_data = np.transpose(np.array(data_capture(conv)))
disable_stingray_channel(sray, subarray_ref)
 

axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100,200])

time.sleep(1)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = rx_gain(sray, conv, subarray, adc_map, sray.element_map)
print("channel_magnitude:", mag_pre_cal)
#enable_stingray_channel(sray, subarray_ref)
#no_cal_data = np.transpose(np.array(data_capture(conv)))
#disable_stingray_channel(sray, subarray_ref)
## plot data with phase delay added post-capture ##
cal_ant = find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
print('peak delay array:',cal_ant)
enable_stingray_channel(sray, subarray_ref)
phase_delay_cal_data = np.array(data_capture(conv))
phase_delay_cal_data = cal_data(phase_delay_cal_data, cal_ant)
phase_delay_cal_data = np.transpose(phase_delay_cal_data)
disable_stingray_channel(sray, subarray_ref)
 
axs[1].plot(phase_delay_cal_data[:,0].real, "red")
axs[1].plot(phase_delay_cal_data[:,1].real, "blue")
axs[1].plot(phase_delay_cal_data[:,2].real, "green")
axs[1].plot(phase_delay_cal_data[:,3].real, "black")
axs[1].set_title('With Phase Delay Added Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_xlim([100,200])
 
# # Plot with digital calibration values assigned to NCO main phase
 
# #digital_phase_cal = phase_digital(sray, conv, adc_ref, subarray_ref)
# print("rx_main_nco_phases now set to:",conv.rx_main_nco_phases)
 
 
# time.sleep(2)
# enable_stingray_channel(sray, subarray)
# analog_phase_pre_cal = np.transpose(np.array(data_capture(conv)))
# time.sleep(2)
# disable_stingray_channel(sray, subarray)
# analog_phase_cal = phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)
 
 
# enable_stingray_channel(sray, subarray)
# analog_phase_cal = np.array(data_capture_cal(conv,cal_ant)).T
# disable_stingray_channel(sray, subarray)
 
 
# def find_zero_crossings(signal):
#     zero_crossings = np.where(np.diff(np.sign(signal)))[0]
#     return zero_crossings
 
# zero_crossings1 = find_zero_crossings(analog_phase_cal[:,0])
# zero_crossings2 = find_zero_crossings(analog_phase_cal[:,1])
# zero_crossings3 = find_zero_crossings(analog_phase_cal[:,2])
# zero_crossings4 = find_zero_crossings(analog_phase_cal[:,3])
 
 
# min_length = min(len(zero_crossings1), len(zero_crossings2),len(zero_crossings3),len(zero_crossings4))
# zero_crossings1 = zero_crossings1[:min_length]
# zero_crossings2 = zero_crossings2[:min_length]
# zero_crossings3 = zero_crossings3[:min_length]
# zero_crossings4 = zero_crossings4[:min_length]
 
# # Calculate sample differences
# sample_differences21 = zero_crossings2 - zero_crossings1
# sample_differences31 = zero_crossings3 - zero_crossings1
# sample_differences41 = zero_crossings4 - zero_crossings1
 
# # Convert sample differences to phase differences (ino_cal_data = np.transpose(np.array(data_capture(conv)))p.pi)
 
# average_sample_shift21 = sample_differences21.mean()
# average_sample_shift31 = sample_differences31.mean()
# average_sample_shift41 = sample_differences41.mean()
 
# def shift_signal(signal, shift):
#     x = np.arange(len(signal))
#     f = interp1d(x, signal, kind='linear', fill_value="extrapolate")
#     #if shift > 0:
#     shifted_x = x + shift
#     #if shift < 0:
#         #shifted_x = x - shift    
#     shifted_signal = f(shifted_x)
#     return shifted_signal
 
 
# # Apply the calculated phase shift to signal2
 
# shifted_signal2 = shift_signal(analog_phase_cal[:,1], average_sample_shift21)
# shifted_signal3 = shift_signal(analog_phase_cal[:,2], average_sample_shift31)
# shifted_signal4 = shift_signal(analog_phase_cal[:,3], average_sample_shift41)
 
# #analog_phase_cal = np.transpose(calibration.cal_data(analog_phase_cal.T,analog_phase_test))
# plt.figure(2)
# #plt.plot(analog_phase_pre_cal[:,0].real, "black")
# plt.plot(analog_phase_cal.real[:,0].real, "blue")
# plt.plot(analog_phase_cal.real[:,1].real, "red")
# plt.plot(analog_phase_cal.real[:,2].real, "green")
# plt.plot(analog_phase_cal.real[:,3].real, "purple")
# plt.title('Analog Phase Calibration')
# plt.xlabel("Index")
# plt.ylabel("Value")
# plt.grid(visible=True)
# plt.xlim([100,200])
 
# plt.figure(3)
# #plt.plot(analog_phase_pre_cal[:,0].real, "black")
# plt.plot(analog_phase_cal.real[:,0].real, "blue")
# plt.plot(shifted_signal2.real, "red")
# plt.plot(shifted_signal3.real, "green")
# plt.plot(shifted_signal4.real, "purple")
# plt.title('Analog Phase Calibration')
# plt.xlabel("Index")
# plt.ylabel("Value")
# plt.grid(visible=True)
# plt.xlim([100,200])
 
# Adjust layout and display
plt.tight_layout()
plt.show()