# Manta Ray 64 Element Electronic Steering Array Calibration and Sweep
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import time
import importlib
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
import mbx_functions as mbx
from scipy.special import factorial
from scipy.io import savemat
import MantaRay as mr


BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB1"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

SELF_BIASED_LNAs = True
ARRAY_MODE = "rx" # start rx cals first
#print("Turn on RF Source...")
#input('Press Enter to continue...')
url = "ip:192.168.0.1"
print("Connecting to", url ,"...")
 
# url = "local:" if len(sys.argv) == 1 else sys.argv[1]
ssh = sshfs(address=url, username="root", password="analog")
 

# Setup Talise RX, TDDN Engine & ADAR1000

 
tddn = adi.tddn(uri = url)
 

fs_RxIQ = 245.76e6;  #I/Q Data Rate in MSPS

# Startup and connect TDDN
tddn.enable = False
tddn.startup_delay_ms = 0
# Configure top level engine
samplesPerFrame = 2**12
frame_length_ms = samplesPerFrame/fs_RxIQ*1000
tddn.frame_length_ms = frame_length_ms
# Configure component channels
on_time = 0
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
# tddn.sync_soft = True

conv = adi.adrv9009_zu11eg(uri = url)
 
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12
conv.dds_phases = []


subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 4
    ])



subarray_ref = np.array([1, 33, 37, 5])  
adc_map      = np.array([0, 1, 2, 3])  # ADC map to subarray
adc_ref      = 0  # ADC reference channel (indexed at 0)

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

delay_phases = np.arange(-180,181,1) # sweep phase from -180 to 180 in 1 degree steps.

mr.disable_stingray_channel(sray)
sray.latch_rx_settings() 
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

sray.steer_rx(azimuth=0, elevation=0) # Broadside # Broadside
# Setup ADXUD1AEBZ and ADF4371
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
adf4371 = ctx.find_device("adf4371-0")
 
# Find channel attribute for TX & RX
txrx1 = xud.find_channel("voltage1", True)
txrx2 = xud.find_channel("voltage2", True)
txrx3 = xud.find_channel("voltage3", True)
txrx4 = xud.find_channel("voltage4", True)
PLLselect = xud.find_channel("voltage5", True)
rxgainmode = xud.find_channel("voltage0", True)
XUDLO = adf4371.find_channel("altvoltage2", True)
 
# 0 for rx, 1 for tx
txrx1.attrs["raw"].value = "0" # Subarray 4print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
txrx2.attrs["raw"].value = "0" # Subarray 3
txrx3.attrs["raw"].value = "0" # Subarray 1
txrx4.attrs["raw"].value = "0" # Subarray 2
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"
XUDLO.attrs["frequency"].value = "14480000000"
XUDLO.attrs["powerdown"].value = "0"


 
#########################################################################
#########################################################################
#### Initilization complete; execute functions for calibration below ####
#########################################################################
# #########################################################################
 
# delay_times = np.arange(-time_max, time_max, time_max/200)    # time delay in ps
#delay_phases = np.arange(-180,181,1) # sweep phase from -180 to 180 in 1 degree steps.
 ############# Insert Phase Calibration here #############


# Enable subarray reference
mr.enable_stingray_channel(sray,subarray)


# Take data capture

no_cal_data = np.transpose(np.array(mr.data_capture(conv)))

# Gain cal
mr.disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(sray, conv, subarray, adc_map, sray.element_map)

# print("Gain Dict Size:", gain_dict.shape)
# print("Mag precal: ", mag_pre_cal)
# print("Mag postcal: ", mag_post_cal)



# Phase cal
print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)



#print('peak delay array:',cal_ant)
mr.enable_stingray_channel(sray)
calibrated_data = np.transpose(np.array(mr.data_capture(conv)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = mr.cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
mr.disable_stingray_channel(sray)


plt.ion()   # Turn on interactive mode
fig, axs = plt.subplots(2,1) # Creates a 2x1 grid of subplots

# Test
mr.enable_stingray_channel(sray)

mr.enable_stingray_channel(sray, subarray)
#no_cal_data = np.transpose(np.array(data_capture(conv)))
 
axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100,600])
axs[1].set_ylim([-28000,28000])

axs[1].plot(calibrated_data.real)
axs[1].set_title('With Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_ylim([-28000,28000])
axs[1].set_xlim([100,600])

# Adjust layout and display
plt.tight_layout()
plt.draw()
plt.pause(0.001) 
plt.show() 
# input("Press Enter to exit...")
# exit() 

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

maxsweepangle = 180
sweepstep = 1
gimbal_motor = GIMBAL_H
sig_gen_freq_GHz=10


steering_angle = 0 # degrees

print("Before Steering Phase:")
print(sray.all_rx_phases)

sray.steer_rx(azimuth=steering_angle, elevation=0) # Steer to desired angle


for element in sray.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))

    # Assign the calculated steered phase to the element
    element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360

sray.latch_rx_settings()  # Latch SPI settings to devices

print("After Steering Phase:")
print(sray.all_rx_phases)

gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)  # Define gimbal positions from -90 to 90 degrees
mbx.move(gimbal_motor,-(maxsweepangle/2))

converter_0 = np.zeros(len(gimbal_positions))
converter_1 = np.zeros(len(gimbal_positions))
converter_2 = np.zeros(len(gimbal_positions))
converter_3 = np.zeros(len(gimbal_positions))

# single_element_sweep = [] # initialize array to hold single element sweep data
steer_data = []
mag_single_sweep = []
peak_mag = np.zeros(len(gimbal_positions))
print(peak_mag.shape)
for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor,sweepstep)
    time.sleep(0.5)  # Allow time for the gimbal to move to the new position

    # disable all but one channel to capture single element data
    mr.disable_stingray_channel(sray)
    mr.enable_stingray_channel(sray, [1])
    data = np.array(mr.data_capture(conv))
    # data_single_sweep = data[0,:]
    # #single_element_sweep.append(mr.get_analog_mag(data))
    # mag_single_sweep[i,:] = mr.get_analog_mag(data_single_sweep)
    # enable all channels to capture steered array data
    mr.disable_stingray_channel(sray)
    mr.enable_stingray_channel(sray, subarray)

    steer_data = np.transpose(np.array(mr.data_capture(conv)))
    # Apply Taylor tapering to the received data
    #steer_data = apply_taylor_taper(steer_data, sidelobe_level=-35)
    steer_data = np.array(steer_data).T
    steer_data = mr.cal_data(steer_data, cal_ant)
    steer_data = np.array(steer_data).T

    combined_data = steer_data[:,0] + steer_data[:,1] + steer_data[:,2] + steer_data[:,3]
    peak_mag[i] = mr.get_analog_mag(combined_data)

    converter_0[i] = mr.get_analog_mag(steer_data[:,0])
    converter_1[i] = mr.get_analog_mag(steer_data[:,1])
    converter_2[i] = mr.get_analog_mag(steer_data[:,2])
    converter_3[i] = mr.get_analog_mag(steer_data[:,3])
    
print(peak_mag.shape)    
mbx.gotoZERO()

# Convert to dBm if needed (assuming -10.2 dBm full scale)
# single_element_sweep_dbm = np.array(single_element_sweep) - 10.2

# Define the corresponding angles
# angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(single_element_sweep_dbm))

# plt.figure(figsize=(10, 6))
# plt.plot(angles, single_element_sweep_dbm, linestyle='dotted', color='green', label='Element 1')
# plt.title('Single Element Azimuth Beam Pattern (Element 1)')
# plt.xlabel('Azimuth Angle (degrees)')
# plt.ylabel('Measured Power (dBm)')
# plt.grid(True)
# plt.legend()
# plt.tight_layout()
# plt.show()

# Calculate peak FFT magnitude for each steering angle
norm_peak_mag = peak_mag - np.max(peak_mag)  # Normalize the peak magnitudes    
    

# Define the corresponding angles (assuming gimbal_positions is 0 to 80, map to -40 to 40)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))



plt.figure(figsize=(10, 6))


# Calculate and plot
mechanical_sweep, elec_steer_angle, azim_results, elev_results, = mr.calc_array_pattern(elec_steer_angle=steering_angle,f_op_GHz=sig_gen_freq_GHz)


# Define steering angles to test
steering_angles = [-60, -45, -30, -15, 0, 15, 30, 45, 60]

# Initialize arrays for both azimuth and elevation
peak_mags_az = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_el = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
azim_results_all = {}
elev_results_all = {}

# === Azimuth Sweep ===
print("Starting Azimuth Sweep...")
gimbal_motor = GIMBAL_H
mbx.gotoZERO()
mbx.move(gimbal_motor,-(maxsweepangle/2))

# Single mechanical sweep for azimuth
for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor, sweepstep)
    time.sleep(0.3)
    
    for steering_angle in steering_angles:
        sray.steer_rx(azimuth=steering_angle, elevation=0)
        
        # Apply analog phase calibration
        for element in sray.elements.values():
            str_channel = str(element)
            value = int(mr.strip_to_last_two_digits(str_channel))
            element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
        sray.latch_rx_settings()

        steer_data = np.transpose(np.array(mr.data_capture(conv)))
        steer_data = np.array(steer_data).T
        steer_data = mr.cal_data(steer_data, cal_ant)
        steer_data = np.array(steer_data).T

        combined_data = np.sum(steer_data,axis=1)
        peak_mags_az[steering_angle][i] = mr.get_analog_mag(combined_data)

mbx.gotoZERO()

# === Elevation Sweep ===
print("Starting Elevation Sweep...")
gimbal_motor = GIMBAL_V
mbx.gotoZERO()
mbx.move(gimbal_motor,-(maxsweepangle/2))

# Single mechanical sweep for elevation
for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor, sweepstep)
    time.sleep(0.3)
    
    for steering_angle in steering_angles:
        sray.steer_rx(azimuth=0, elevation=steering_angle)
        
        # Apply analog phase calibration
        for element in sray.elements.values():
            str_channel = str(element)
            value = int(mr.strip_to_last_two_digits(str_channel))
            element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
        sray.latch_rx_settings()

        steer_data = np.transpose(np.array(mr.data_capture(conv)))
        steer_data = np.array(steer_data).T
        steer_data = mr.cal_data(steer_data, cal_ant)
        steer_data = np.array(steer_data).T

        combined_data = np.sum(steer_data, axis=1)
        peak_mags_el[steering_angle][i] = mr.get_analog_mag(combined_data)

mbx.gotoZERO()

# Save data to MATLAB file with both azimuth and elevation patterns
matlab_data = {
    'mechanical_angles': angles,
    'steering_angles': steering_angles,
    'cal_antenna': cal_ant,
    # Azimuth patterns (convert to dBm)
    'measured_patterns_az_neg60': peak_mags_az[-60] - 10.2,
    'measured_patterns_az_neg45': peak_mags_az[-45] - 10.2,
    'measured_patterns_az_neg30': peak_mags_az[-30] - 10.2,
    'measured_patterns_az_neg15': peak_mags_az[-15] - 10.2,
    'measured_patterns_az_0': peak_mags_az[0] - 10.2,
    'measured_patterns_az_pos15': peak_mags_az[15] - 10.2,
    'measured_patterns_az_pos30': peak_mags_az[30] - 10.2,
    'measured_patterns_az_pos45': peak_mags_az[45] - 10.2,
    'measured_patterns_az_pos60': peak_mags_az[60] - 10.2,
    # Elevation patterns (convert to dBm)
    'measured_patterns_el_neg60': peak_mags_el[-60] - 10.2,
    'measured_patterns_el_neg45': peak_mags_el[-45] - 10.2,
    'measured_patterns_el_neg30': peak_mags_el[-30] - 10.2,
    'measured_patterns_el_neg15': peak_mags_el[-15] - 10.2,
    'measured_patterns_el_0': peak_mags_el[0] - 10.2,
    'measured_patterns_el_pos15': peak_mags_el[15] - 10.2,
    'measured_patterns_el_pos30': peak_mags_el[30] - 10.2,
    'measured_patterns_el_pos45': peak_mags_el[45] - 10.2,
    'measured_patterns_el_pos60': peak_mags_el[60] - 10.2
}

# Save combined azimuth and elevation data
savemat('/home/snuc/Desktop/beamforming_patterns_azel.mat', matlab_data)

# Create plots for both azimuth and elevation patterns
plt.ioff()  # Turn off interactive mode for batch saving

# Plot and save azimuth patterns
for steering_angle in steering_angles:
    plt.figure(figsize=(10, 6))
    plt.plot(angles, peak_mags_az[steering_angle] - 10.2,  # Convert to dBm
             linestyle='dotted', label='Measured Data', 
             color='blue', markersize=9)
    plt.title(f'Azimuth Pattern (Steering Angle: {steering_angle}°)')
    plt.xlabel('Mechanical Azimuth Angle (degrees)')
    plt.ylabel('Combined RF Input Power (dBm)')
    plt.ylim(-60, 0)
    plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'/home/snuc/Desktop/azimuth_pattern_{steering_angle}deg.png')
    plt.close()

# Plot and save elevation patterns
for steering_angle in steering_angles:
    plt.figure(figsize=(10, 6))
    plt.plot(angles, peak_mags_el[steering_angle] - 10.2,  # Convert to dBm
             linestyle='dotted', label='Measured Data', 
             color='red', markersize=9)
    plt.title(f'Elevation Pattern (Steering Angle: {steering_angle}°)')
    plt.xlabel('Mechanical Elevation Angle (degrees)')
    plt.ylabel('Combined RF Input Power (dBm)')
    plt.ylim(-60, 0)
    plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'/home/snuc/Desktop/elevation_pattern_{steering_angle}deg.png')
    plt.close()