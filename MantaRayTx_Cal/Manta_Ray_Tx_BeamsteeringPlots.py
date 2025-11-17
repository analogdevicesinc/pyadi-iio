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
import E36233A_Driver as E36233A
import N9000A_Driver as N9000A
import N6705B_Driver as N6705B
import pyvisa
import math
rm = pyvisa.ResourceManager()

BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB0"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

##############################################
## Step 0: Initialize Power Supplies ##
###############################################
E36 = "TCPIP::192.168.1.35::inst0::INSTR"
PA_Supplies = E36233A.E36233A(rm, E36)
PA_Supplies.output_off(1)


#18 Volt Rail (for some reason, setting current isn't working)
PA_Supplies.set_voltage(1,18)
PA_Supplies.set_current(1,30)


## Keysight N6705B Power Supply (modular) for Manta Ray Rails ##
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)
Pwr_Supplies.output_off(3)

CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
# PSG = "TCPIP0::192.168.20.25::inst0::INSTR"

SpecAn = N9000A.N9000A(rm, CXA)


SELF_BIASED_LNAs = True

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

maxsweepangle = 120
sweepstep = 5
gimbal_motor = GIMBAL_H
sig_gen_freq_GHz=10
steering_angle = 0 # degrees

talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip
sdr  = adi.adrv9009_zu11eg(talise_uri)
ctx = sdr._ctrl.ctx



dev = adi.adar1000_array(
    uri = talise_uri,
    
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

talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip
# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
sdr.tx_hardwaregain_chan0 = -5
sdr.tx_hardwaregain_chan1 = -5
sdr.tx_hardwaregain_chan0_chip_b = -5
sdr.tx_hardwaregain_chan1_chip_b = -5


# analog_phase_vals_tx = []
# for element in dev.elements.values():
#     str_channel = str(element)
#     value = int(mr.strip_to_last_two_digits(str_channel))
#     analog_phase_vals_tx.append(element.tx_phase)

# mr.create_dict()
#     # Assign the calculated steered phase to the element
#     element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360


# for element in dev.elements.values():
#     str_channel = str(element)
#     value = int(mr.strip_to_last_two_digits(str_channel))

#     # Assign the calculated steered phase to the element
#     element.rx_phase = (steering_angle - element.tx_phase) % 360

# dev.steer_tx(azimuth=steering_angle, elevation=0) # Steer to desired angle

### Setup Spec An ##


SpecAn.reset()  

SpecAn.set_to_spec_an_mode() 
SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
# SpecAn_Res_BW = 10e3
SpecAn_Res_BW = 8e6    #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
NumChannels = 4   #Set to number of channels being used #Reset instrument
SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency
## Set span to 10 MHz for spectrum analyzer mode ##
SpecAn.write("SENS:FREQ:SPAN 500E3")
# SpecAn.set_resolution_bandwidth(9e-3)
SpecAn.set_resolution_bandwidth(8)
SpecAn.set_continuous_peak_search(1,1)



gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)  # Define gimbal positions from -90 to 90 degrees
mbx.move(gimbal_motor,-(maxsweepangle/2))
SpecAn_Values = []

## Center 4x4 array ##
# active_array = [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46]
## Center 6x6 array ##
# active_array = [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46,10, 18, 26, 34, 42, 50, 51, 52, 53, 54, 55, 47, 39, 31, 23, 15, 14, 13, 12, 11]
## Full 8x8 array ##
# active_array = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64]

array_shapes =[[19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46], 
              [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46,10, 18, 26, 34, 42, 50, 51, 52, 53, 54, 55, 47, 39, 31, 23, 15, 14, 13, 12, 11],
              [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64],
              [1,2,3,4,5,6,7,8,9,17,25,33,41,49,57,58,59,60,61,62,63,64,56,48,40,32,24,16]
              ]

## Enter desired array shape here: "4x4", "6x6", "8x8", or "outer" ##
desired_array_shape = "8x8"

if desired_array_shape == "4x4":
    active_array = array_shapes[0]
elif desired_array_shape == "6x6":
    active_array = array_shapes[1]
    SpecAn.set_reference_level(0)
elif desired_array_shape == "8x8":
    active_array = array_shapes[2]
    SpecAn.set_reference_level(10)
elif desired_array_shape == "outer":
    active_array = array_shapes[3]
    SpecAn.set_reference_level(10)




mr.disable_pa_bias_channel(dev)
PA_Supplies.output_on(1)

a=1
a=1


for i in range(len(gimbal_positions)):
    try:
        mr.enable_pa_bias_channel(dev, active_array)


        time.sleep(5)
        tone_value = SpecAn.get_marker_power(marker=1)
        SpecAn_Values.append(tone_value)
        print(tone_value)
        mbx.move(gimbal_motor,sweepstep)


        mr.disable_pa_bias_channel(dev, active_array)
        time.sleep(3)
    except Exception as e:
        print(f"Unexpected error in sweep loop at index {i}: {e}")
        # Ensure supplies are turned off on error
        PA_Supplies.output_off(1)
        mr.disable_pa_bias_channel(dev)
        exit()

    
a=1
peak_mag = SpecAn_Values
mr.disable_pa_bias_channel(dev)
# exit()    
    
# print(peak_mag.shape)    
# mbx.gotoZERO()

# Convert to dBm if needed (assuming -10.2 dBm full scale)
# single_element_sweep_dbm = np.array(single_element_sweep) - 10.2

# Define the corresponding anglesSpecAn_Values
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(peak_mag))

plt.figure(figsize=(10, 6))
plt.plot(angles, peak_mag, linestyle='dotted', color='green', label='Element 1')
plt.title(f'{desired_array_shape} Element Azimuth Beam Pattern')
plt.xlabel('Azimuth Angle (degrees)')
plt.ylabel('Measured Power (dBm)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()




# Calculate peak FFT magnitude for each steering angle
norm_peak_mag = peak_mag - np.max(peak_mag)  # Normalize the peak magnitudes    
    

# Define the corresponding angles (assuming gimbal_positions is 0 to 80, map to -40 to 40)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))



plt.figure(figsize=(10, 6))
exit()

# Calculate and plot
mechanical_sweep, elec_steer_angle, azim_results, elev_results, = mr.calc_array_pattern(elec_steer_angle=steering_angle,f_op_GHz=sig_gen_freq_GHz)


# Define steering angles to test
steering_angles = [-60, -45, -30, -15, 0, 15, 30, 45, 60]

# Initialize arrays for both azimuth and elevation
peak_mags_az = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_el = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
azim_results_all = {}
elev_results_all = {}

# # === Azimuth Sweep ===
# print("Starting Azimuth Sweep...")
# gimbal_motor = GIMBAL_H
# mbx.gotoZERO()
# mbx.move(gimbal_motor,-(maxsweepangle/2))

# # Single mechanical sweep for azimuth
# for i in range(len(gimbal_positions)):
#     mbx.move(gimbal_motor, sweepstep)
#     time.sleep(0.3)
    
#     for steering_angle in steering_angles:
#         sray.steer_rx(azimuth=steering_angle, elevation=0)
        
#         # Apply analog phase calibration
#         for element in sray.elements.values():
#             str_channel = str(element)
#             value = int(mr.strip_to_last_two_digits(str_channel))
#             element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
#         sray.latch_rx_settings()

#         steer_data = np.transpose(np.array(mr.data_capture(conv)))
#         steer_data = np.array(steer_data).T
#         steer_data = mr.cal_data(steer_data, cal_ant)
#         steer_data = np.array(steer_data).T

#         combined_data = np.sum(steer_data,axis=1)
#         peak_mags_az[steering_angle][i] = mr.get_analog_mag(combined_data)

# mbx.gotoZERO()

# # === Elevation Sweep ===
# print("Starting Elevation Sweep...")
# gimbal_motor = GIMBAL_V
# mbx.gotoZERO()
# mbx.move(gimbal_motor,-(maxsweepangle/2))

# # Single mechanical sweep for elevation
# for i in range(len(gimbal_positions)):
#     mbx.move(gimbal_motor, sweepstep)
#     time.sleep(0.3)
    
#     for steering_angle in steering_angles:
#         sray.steer_rx(azimuth=0, elevation=steering_angle)
        
#         # Apply analog phase calibration
#         for element in sray.elements.values():
#             str_channel = str(element)
#             value = int(mr.strip_to_last_two_digits(str_channel))
#             element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
#         sray.latch_rx_settings()

#         steer_data = np.transpose(np.array(mr.data_capture(conv)))
#         steer_data = np.array(steer_data).T
#         steer_data = mr.cal_data(steer_data, cal_ant)
#         steer_data = np.array(steer_data).T

#         combined_data = np.sum(steer_data, axis=1)
#         peak_mags_el[steering_angle][i] = mr.get_analog_mag(combined_data)

# mbx.gotoZERO()

# Save data to MATLAB file with both azimuth and elevation patterns
matlab_data = {
    'mechanical_angles': angles,
    'steering_angles': steering_angles,
    # 'cal_antenna': cal_ant,
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