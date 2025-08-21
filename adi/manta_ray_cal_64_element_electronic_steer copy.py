#Dual Stingray Mirror
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



BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB0"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()
# input("Press any key to continue...")



def enable_stingray_channel(obj, elements=None, man_input=False):
    """
    Enables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn on (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    elif man_input is False and elements is None:
        elements = elements=list(range(1,65))

    else:
        elements = np.array(elements).flatten()

    for i in range(10):
        try:
            for device in obj.devices.values():
                # time.sleep(0.01)
                if device.mode == "rx":
                    for channel in device.channels:

                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                # print("Turning on element:",elem)
                                channel.rx_enable = True

                if device.mode == "tx":
                    for channel in device.channels:

                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                channel.tx_enable = Trueflat
                # else:
                #     raise ValueError('Mode of operation must be either "rx" or "tx"')
            break
        except:
            print("retrying")
            time.sleep(2)
    else:
        raise ValueError('Mode of operation must be either "rx" or "tx"')
 
# Receive data on AD9081
def data_capture(adc):
    adc.rx_destroy_buffer() # clear previous data
    for i in range(2):
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    
    return data


def disable_stingray_channel(obj, elements=None, man_input=False):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn off (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    elif man_input is False and elements is None:
        elements = elements=list(range(1,65))

    else:
        elements = np.array(elements).flatten()

    for i in range(10):
        try:
            for device in obj.devices.values():
                time.sleep(0.01)
                if device.mode == "rx":
                    for channel in device.channels:

                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                # print("Turning off element:",elem)
                                channel.rx_enable = False

                if device.mode == "tx":
                    for channel in device.channels:

                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                channel.tx_enable = False
                # else:
                #     raise ValueError('Mode of operation must be either "rx" or "tx"')
            break
        except:
            print("retrying")
            time.sleep(2)
    else:
        raise ValueError('Mode of operation must be either "rx" or "tx"')
        
# Receive data on AD9081
def data_capture_cal(adc, cal_values):
    adc.rx_destroy_buffer() # clear previous data
    for i in range(2):
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    data = cal_data(data, cal_values) # only do phase delay cals, no gain
    return data
 
# Add phasor with delay to complex data
def phase_delayer(data, delay):
    # Adds phase delay in degrees
    delayed_data = data * np.exp(1j*np.deg2rad(delay))
    return delayed_data

# Calibrate the data using phase and gain calibration values
def cal_data(data, phaseCAL):
    for i in range(len(data)):
        #data[i] = phase_delayer(data[i]*gainCal[i], phaseCAL[i])
        data[i] = phase_delayer(data[i], phaseCAL[i])
    return data

# def gain_codes(obj, analog_mag_pre_cal, mode):
#     """
#     Determines Rx/Tx analog VGA gain codes for Stingray.
#     Returns calibrated gain codes and attenuation values.
#     """
#     analog_mag_pre_cal = analog_mag_pre_cal.flatten()
#     mag_db = 20 * np.log10(np.maximum(analog_mag_pre_cal, 1e-12))

#     target_db = np.mean(mag_db)
#     mag_cal_diff_db = mag_db - target_db
#     atten = np.zeros_like(mag_cal_diff_db)

#     # Simplified polynomial fit or linear mapping
#     def map_gain(diff_db):
#         if abs(diff_db) < 12:
#             return np.clip(np.floor(127 - diff_db / 0.45), 0, 127)
#         else:
#             atten_flag = 1
#             return np.clip(np.floor(127 - (diff_db - 15) / 0.45), 0, 127), atten_flag

#     gain_codes_cal = np.zeros_like(mag_cal_diff_db)
#     for i, diff_db in enumerate(mag_cal_diff_db):
#         if abs(diff_db) < 12:
#             gain_codes_cal[i] = map_gain(diff_db)
#         else:
#             gain_codes_cal[i], atten[i] = map_gain(diff_db)

#     return gain_codes_cal.astype(int), atten.astype(int)


def gain_codes(obj, analog_mag_pre_cal, mode):
    """array.
    gainCodes  Determines Rx/Tx analog VGA gain codes for Stingray
    Help: returns calibrated gain codes and attenuation values.
    """
    atten = np.zeros(np.shape(analog_mag_pre_cal))
   
    # Polynomial fit coefficients for Rx and Tx modes
    if mode == "rx":
        poly_atten1 = [-4.178368227245296e-09, -3.124456767699238e-07, -7.218061870232358e-06,
                     1.146280656652001e-05, 0.003079353177989, 0.048281159204065,
                     0.247215102895886, 0.176811045216789, 10.163992861226674, 127.1237461140638]
        poly_atten0 = [4.12957161960063e-10, 1.11191262836380e-07, 1.34714959988008e-05,
                     0.000967813015434471, 0.0456701602403594, 1.47865205676699,
                     33.2281071820574, 510.768971360134, 5126.75849430329, 30268.0388934082, 79815.3362477404]
    elif mode == "tx":
        poly_atten1 = [2.11066024918707e-11, 5.70009839945272e-09, 5.49937839434060e-07,
                     2.73783996444945e-05, 0.000800103462132557, 0.0143895847100511,
                     0.159688022065331, 1.06808692792217, 4.50865732789487,
                     21.0313863981928, 127.541504127078]
        poly_atten0 = [5.00901188825329e-10, 1.44673726954726e-07, 1.86493751074489e-05,
                     0.00141263342869073, 0.0696128076080524, 2.33122230277517,
                     53.7090182591208, 840.244043642996, 8539.25517554357,    
                     50904.6416796854, 135350.366810770]
 
    # Calculate delta in dB
    # analog_mag_pre_cal = analog_mag_pre_cal.flatten() 
    analog_mag_pre_cal = analog_mag_pre_cal.flatten()
    # for i in range(np.size(analog_mag_pre_cal)):
    #     if analog_mag_pre_cal[i] < np.average(analog_mag_pre_cal) - 12:
    #         print("Bad Value: ", analog_mag_pre_cal[i])
    #         print("Index Number: ", i)
    #         analog_mag_pre_cal[i] = np.average(analog_mag_pre_cal)

    # mag_min = np.min(analog_mag_pre_cal)
    # mag_cal_diff = analog_mag_pre_cal - mag_min
    # print(mag_cal_diff)

    # Calculate the target magnitude as the median of the pre-calibration magnitudes
    target_mag = np.median(analog_mag_pre_cal)
    mag_cal_diff = analog_mag_pre_cal - target_mag
    
    mag_cal_poly = np.zeros(np.shape(analog_mag_pre_cal))
    # print(mag_min)
    # Find correct gain code values based on which polynomial should be used
    # Adjust attenuators accordingly
    for i in range(np.size(analog_mag_pre_cal)):
        #mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten1, -1 * mag_cal_diff.flat[i]))
        #mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten1, mag_cal_diff.flat[i]))
        mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten1, -1 * mag_cal_diff[i]))
        # if mag_cal_diff.flat[i] < 23:
        #     mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten1, -1 * mag_cal_diff.flat[i]))

        # elif mag_cal_diff.flat[i] == np.inf:
        #     mag_cal_poly.flat[i] = 0
        #     atten.flat[i] = 1
            
        # else:
        #     mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten0, -1 * mag_cal_diff.flat[i]))
        #     atten.flat[i] = 1
    # set min and max clipping to 0 and 127, respectively
    mag_cal_poly = np.clip(mag_cal_poly, 0, 127)
    gain_codes_cal = mag_cal_poly

    atten = np.zeros(np.shape(analog_mag_pre_cal))
    return gain_codes_cal, atten 

def strip_to_last_two_digits(input_string):
    """
    Extract the last two digits from a string.
    """
    # Find all sequences of digits in the string
    all_numbers = re.findall(r'\d+', input_string)

    # Join them together and take the last two digits
    last_two_digits = ''.join(all_numbers)[-2:]
    
    return last_two_digits

def create_dict(new_keys, array):
    """
    Convert a flattened array (1x64) into 8x8 and create a dictionary 
    where each key from new_keys (8x8) maps to its corresponding 8-value row.
    """
    result_dict = {}
    print(array)
    print(new_keys)
    # Reshape new_keys and array into 8x8
    reshaped_keys = new_keys.reshape(8, 8,order='F')
    reshaped_array = array.reshape(8, 8,order='F')

    # Map each key in reshaped_keys to the corresponding row in reshaped_array
    for i in range(8):
        for j in range(8):
            result_dict[reshaped_keys[i][j]] = reshaped_array[i][j]
    
    return result_dict

def wrap_to_360(angle):
    """Wrap angle to the range [0, 360)."""
    return angle % 360

def ind2sub(array_shape, index):
    """Convert a linear index to row and column indices."""
    rows = index % array_shape[0]
    cols = index // array_shape[0]
    return rows, cols

####################################################################################################
#               RX signal-chain calibration functions for the X-Band Development Kit               #
####################################################################################################

# Calculates dBFS spectrum for 12-bit signed ADC data
def calc_dbfs(data):
    # Calculates dBFS spectrum for 12-bit signed ADC data
    NumSamples = len(data)
    win = np.hamming(NumSamples)
    y = data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    
    # Avoid log(0)
    s_mag = np.abs(s_shift)
    s_mag[s_mag == 0] = 1e-12

    # Convert to dBFS
    s_dbfs = 20 * np.log10(s_mag / (2**11))  # 2^11 = 2048 (full scale peak for signed 12-bit)
    return s_dbfs

def find_phase_delay_sliding_ref(obj, adc, subarray_ref, adc_map, delay_phases):
    """
    Measures calibrated phase offsets for Stingray reference channels in units of degrees using sliding reference.
    """

    # Enable the Stingray reference channels and capture data
    enable_stingray_channel(obj,subarray_ref)
    data = np.array(data_capture(adc))

    # Create a list to store the calibration values for each antenna
    # Initialize the first antenna's calibration value to 0
    cal_ant = []
    cal_ant.append(0)

    for i in range(len(data)-1):
        peak_sum = []
        for phase_delay in delay_phases:

            # Apply the phase delay to the first and second antennas
            first_ant = phase_delayer(data[adc_map[i]], phase_delay*i+cal_ant[i])
            second_ant = phase_delayer(data[adc_map[i+1]], phase_delay*(i+1))

            # Calculate the delayed sum of the two antennas
            # and find the maximum value
            delayed_sum = calc_dbfs(first_ant - second_ant)
            peak_sum.append(np.max(delayed_sum))

        # Find the minimum value in the peak sum and its index
        # This index corresponds to the phase delay that minimizes the difference
        null_val = np.min(peak_sum)
        null_index = np.where(peak_sum==null_val)

    # Disable the Stingray reference channels
    disable_stingray_channel(obj,subarray_ref)
    return cal_ant

def find_phase_delay_fixed_ref(obj, adc, subarray_ref, adc_ref, delay_phases):
    """
    Measures calibrated phase offsets for Stingray reference channels in units of degrees using fixed reference.
    """
    # Enable the Stingray reference channels and capture data
    enable_stingray_channel(obj,subarray_ref)
    data = np.array(data_capture(adc))

    # Create a list to store the calibration values for each antenna
    # Initialize the first antenna's calibration value to 0
    cal_ant = []
    cal_ant.append(0)

    # Apply a zero phase delay to the reference antenna
    first_ant = phase_delayer(data[adc_ref], cal_ant[0])

    for i in range(len(data)):
        peak_sum = []
        for phase_delay in delay_phases:

            # Apply the phase delay second antennas
            second_ant = phase_delayer(data[i], phase_delay)

            # Calculate the delayed sum of the two antennas
            delayed_sum = calc_dbfs(first_ant - second_ant)

            # Find the maximum value
            peak_sum.append(np.max(delayed_sum))
        
        # Find the minimum value in the peak sum and its index
        null_val = np.min(peak_sum)
        null_index = np.where(np.abs(peak_sum)==np.abs(null_val))

        # Get the phase delay value that corresponds to the minimum peak sum
        # and append it to the calibration values list
        cal_value = delay_phases[null_index]
        cal_ant.append(cal_value[0].item())

    # Disable the Stingray reference channels
    disable_stingray_channel(obj,subarray_ref)
    cal_ant = cal_ant[1:]
    # Roll the calibration values to align with the reference antenna
    # This is done because data[adc_ref] corresponds to subarray 4
    #return np.roll(cal_ant, -1)
    return cal_ant

def phase_digital(obj, adc, adc_ref, subarray_ref):
    """
    Measures calibrated phase offsets for AD9081 in units of milli-degrees.
    Returns digital phase offsets in a 1x4 row vector
    """
    # Enable analog array_reference channels for NCO calibration
    enable_stingray_channel(obj, subarray_ref)

    # Capture ADC data
    data = np.array(data_capture(adc))

    # Extract sample 100 from each IQ, phase in degrees
    phase_compare = np.angle(data[:, 100], deg = True)

    # Measure phase delta with respect to reference and scale to millidegrees
    digital_phase_cal = (np.mod(phase_compare - phase_compare[adc_ref] + 180, 360) - 180) * 1e3

    # Disable analog array_reference channels
    disable_stingray_channel(obj, subarray_ref)

    # write NCO phases to AD9081
    adc.rx_main_nco_phases = (np.round(digital_phase_cal).astype(int)).tolist()
 
    return digital_phase_cal

def get_gain_codes(obj,adc,subarray,adc_map):

    null_gain_dict = np.zeros((1, np.size(subarray,0)))

    gain_dict = create_dict(subarray, null_gain_dict)

    for element in obj.elements.values():
        """
        Iterate through each element in the Stingray object
        Convert the element to a string and extract the last two digits
        This is used to map the element to its corresponding gain and attenuation values
        in the dictionaries created above
        """

        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))
        if value in subarray:
            value = int(strip_to_last_two_digits(str_channel))

            element.rx_attenuator = atten_dict[value]
            element.rx_gain = gain_dict[value]

            obj.latch_rx_settings() # Latch SPI settings to devices

# def rx_gain(obj, adc, subarray, adc_map, element_map, gain_codes_offset,
#             vga_step_db=0.45, max_iter=5, spread_thresh=0.1):
#     """
#     Refined RX gain calibration using ADAR1000 resolution info.
#     - vga_step_db: ~0.45 dB per VGA code step.
#     - Uses VGA + optional ±15 dB attenuator.
#     - Iterates until spread < spread_thresh or max_iter reached.
#     """
#     data = rx_single_channel_data(obj, adc, subarray, adc_map)
#     analog_mag_pre = get_analog_mag(data)
#     analog_mag_curr = analog_mag_pre.copy()

#     gain_codes_cal, atten_cal = gain_codes(obj, analog_mag_pre, "rx")

#     for iteration in range(max_iter):
#         # Apply settings to hardware
#         gain_dict = create_dict(element_map, gain_codes_cal)
#         atten_dict = create_dict(element_map, atten_cal)
#         for element in obj.elements.values():
#             ch = int(strip_to_last_two_digits(str(element)))
#             if ch in subarray:
#                 element.rx_gain = gain_dict[ch]
#                 element.rx_attenuator = atten_dict[ch]
#         obj.latch_rx_settings()

#         # Measure current magnitudes
#         data = rx_single_channel_data(obj, adc, subarray, adc_map)
#         analog_mag_curr = get_analog_mag(data)
#         mag_db = 20 * np.log10(analog_mag_curr + 1e-12)

#         # Smooth magnitude to reduce noise
#         mag_db_smooth = np.convolve(mag_db, np.ones(3)/3, mode='same')

#         target_db = np.mean(mag_db_smooth)
#         residual = mag_db_smooth - target_db

#         # VGA corrections
#         vga_corrections = np.round(-residual / vga_step_db).astype(int)
#         gain_codes_cal = np.clip(gain_codes_cal + vga_corrections, 0, 127)

#         # Attenuator logic with hysteresis
#         atten_corrections = np.zeros_like(residual)
#         atten_corrections[residual > 8] = 1
#         atten_corrections[residual < -8] = 0
#         atten_cal = atten_corrections

#         # Spread metric: 90% range
#         spread = np.percentile(mag_db_smooth, 95) - np.percentile(mag_db_smooth, 5)
#         print(f"Iter {iteration+1}: spread = {spread:.3f} dB")

#         if spread < spread_thresh:
#             break

#     analog_mag_post = analog_mag_curr
#     return gain_codes_cal, atten_cal, analog_mag_pre, analog_mag_post

## Original cal to minimum ampltiude across 4 channels ##
def rx_gain(obj, adc, subarray, adc_map, element_map):
    """
    Measures analog magnitude for Stingray to equalize amplitudes across all elements.
    Returns calibrated gain codes and magnitude in dBFS pre-calibration in an 8x8 matrix mapped to the Stingray elements.
    """
    
    # Capture ADC data with initial gain, attenuation, and phase settings
    data = rx_single_channel_data(obj, adc, subarray, adc_map)

    # Measure analog magnitude pre-calibration
    analog_mag_pre_cal = get_analog_mag(data)
    # Reshape the analog magnitude to match the subarray shape in column-major order
    # This is necessary to match the element_map mapping
    analog_mag_pre_cal0 = np.reshape(analog_mag_pre_cal, np.shape(element_map), order = 'F')
    # Calculate gain codes and attenuation values based on pre-calibration magnitude
    gain_codes_cal, atten_cal = gain_codes(obj, analog_mag_pre_cal, "rx")
    print(gain_codes_cal)
    # Create dictionary to assign gain codes and attenuation values to elements
    gain_dict = create_dict(element_map, gain_codes_cal)
    print("gain_dict:", gain_dict)
    atten_dict = create_dict(element_map, atten_cal)
    # print("atten_dict:", atten_dict)

    for element in obj.elements.values():
        """
        Iterate through each element in the Stingray object
        Convert the element to a string and extract the last two digits
        This is used to map the element to its corresponding gain and attenuation values
        in the dictionaries created above
        """
        str_channel = str(element)
        
        value = int(strip_to_last_two_digits(str_channel))

        element.rx_attenuator = atten_dict[value]
        element.rx_gain = gain_dict[value]

        obj.latch_rx_settings() # Latch SPI settings to devices
   
    # Capture ADC data with calibrated gain codes and attenuation values
    data = rx_single_channel_data(obj, adc, subarray, adc_map)
   
    # Measure analog magnitude post-calibration
    analog_mag_post_cal = get_analog_mag(data)
    analog_mag_post_cal0 = np.reshape(analog_mag_post_cal, np.shape(element_map), order = 'F')

    print("PreCal Data before Reshape:", analog_mag_pre_cal,)
    print("PreCal Data after Reshape:",analog_mag_pre_cal0)
    print("Postcal Data before Reshape:", analog_mag_post_cal,)
    print("PostCal Data after Reshape:",analog_mag_post_cal0)
 
    return gain_codes_cal, atten_cal, analog_mag_pre_cal, analog_mag_post_cal

# def rx_gain(obj, adc, subarray, adc_map, element_map,gain_codes_offset):
#     """
#     Measures analog magnitude for Stingray to equalize amplitudes across all elements.
#     Returns calibrated gain codes and magnitude in dBFS pre-calibration in an 8x8 matrix mapped to the Stingray elements.
#     """

#     # Capture ADC data with initial gain, attenuation, and phase settings
#     data = rx_single_channel_data(obj, adc, subarray, adc_map)

#     # Measure analog magnitude pre-calibration
#     analog_mag_pre_cal = get_analog_mag(data)
#     # Reshape the analog magnitude to match the subarray shape in column-major order
#     # This is necessary to match the element_map mapping
#     # analog_mag_pre_cal0 = np.reshape(analog_mag_pre_cal, np.shape(element_map), order = 'C')
#     # Calculate gain codes and attenuation values based on pre-calibration magnitude


    



#     gain_codes_cal, atten_cal = gain_codes(obj, analog_mag_pre_cal, "rx")
#     print(gain_codes_cal)
    

#     # Create dictionary to assign gain codes and attenuation values to elements
#     gain_dict = create_dict(element_map, gain_codes_cal)
#     print("gain_dict:", gain_dict)
#     atten_dict = create_dict(element_map, atten_cal)
#     # print("atten_dict:", atten_dict)



#     for element in obj.elements.values():
#         """
#         Iterate through each element in the Stingray object
#         Convert the element to a string and extract the last two digits
#         This is used to map the element to its corresponding gain and attenuation values
#         in the dictionaries created above
#         """

#         str_channel = str(element)
#         value = int(strip_to_last_two_digits(str_channel))
#         if value in subarray:
#             value = int(strip_to_last_two_digits(str_channel))

#             element.rx_attenuator = atten_dict[value]
#             element.rx_gain = gain_dict[value]

#             obj.latch_rx_settings() # Latch SPI settings to devices
   
#     # Capture ADC data with calibrated gain codes and attenuation values
#     sray.latch_rx_settings() # Latch SPI settings to devices
#     data = rx_single_channel_data(obj, adc, subarray, adc_map)

#     # Measure analog magnitude post-calibration
#     analog_mag_post_cal = get_analog_mag(data)
 
#     return gain_codes_cal, atten_cal, analog_mag_pre_cal, analog_mag_post_cal

def phase_analog(sray_obj, adc_obj, adc_map, adc_ref, subarray_ref, subarray_targ, dig_phase):
    """Calculate analog phase for each element in the subarray."""
    analog_phase = np.zeros((4, 16))  # Initialize phase array
    element_map = np.array([
        [1, 9,  17, 25, 33, 41, 49, 57],
        [2, 10, 18, 26, 34, 42, 50, 58],
        [3, 11, 19, 27, 35, 43, 51, 59],
        [4, 12, 20, 28, 36, 44, 52, 60],
 
        [5, 13, 21, 29, 37, 45, 53, 61],
        [6, 14, 22, 30, 38, 46, 54, 62],
        [7, 15, 23, 31, 39, 47, 55, 63],
        [8, 16, 24, 32, 40, 48, 56, 64]
        ])
    # break out subarray 1 cal, vs subarrays 2,3,4 cal
    for ii in range(2): 
        for jj in range(subarray_targ.shape[1]):
            dummy_array = np.zeros((4, 16))

            if ii == 0:

                # When calibrating subarray 1, use the reference channel from subarray 2
                tmp_array_ref = subarray_ref[1]

                # Assign the target channels from subarray 1 to tmp_targ
                tmp_targ = subarray_targ[0, :]

                # Enable the reference channel in subarray 2
                enable_stingray_channel(sray_obj, tmp_array_ref)

                # Iterate through subarray 1 and enable one channel at a time (excludes the reference channel)
                enable_stingray_channel(sray_obj, tmp_targ[jj])

                # Grab row and column indices for specific channel in subarray 1
                row, col = ind2sub(dummy_array.shape, tmp_targ[jj] - 1)

            else:

                # When calibrating subarrays 2, 3, and 4, use the reference channel from subarray 1
                tmp_array_ref = subarray_ref[0]

                # Assign the target channels from subarray 2, 3, and 4 to tmp_targ
                tmp_targ = subarray_targ[1:4]

                # Enable the reference channel in subarray 1
                enable_stingray_channel(sray_obj, tmp_array_ref)

                # Enable the target channels in subarray 2, 3, and 4
                enable_stingray_channel(sray_obj, tmp_targ[:, jj])

                # Grab row and column indices for specfic channel in subarray 2, 3, and 4
                row, col = ind2sub(dummy_array.shape, tmp_targ[:, jj] - 1)

            # Capture ADC data for the enabled channels
            data = data_capture_cal(adc_obj, dig_phase)
            data = np.array(data).T

            # Extract the phase information from the captured data and convert to degrees
            phase_compare = np.angle(data[100, :]) * 180 / np.pi

            if ii == 0:
                # When calibrating subarray 1, use the reference channel from subarray 2
                # analog_phase[row, col] = wrap_to_360(phase_compare[adc_map[0]] - phase_compare[adc_map[1]])
                analog_phase[0, jj+1] = wrap_to_360(phase_compare[adc_map[0]] - phase_compare[adc_map[1]])
            else:
                for n in range(1, len(adc_map)):
                    # When calibrating subarrays 2, 3, and 4, use the reference channel from subarray 4
                    # analog_phase[row, col] = wrap_to_360(phase_compare[adc_map[n]] - phase_compare[adc_ref])
                    analog_phase[n, jj+1] = wrap_to_360(phase_compare[adc_map[n]] - phase_compare[adc_ref])

            if ii == 0:
                # Disable the target channel in subarray 1
                disable_stingray_channel(sray_obj, tmp_targ[jj])
            else:
                # Disable the target channels in subarrays 2, 3, and 4
                disable_stingray_channel(sray_obj, tmp_targ[:, jj])

        # Disable the reference channel being used for calibration
        disable_stingray_channel(sray_obj, tmp_array_ref)

    # analog_phase_dummy = [analog_phase[0,0:3],analog_phase[3,0:3]]
                      
    analog_phase_flatten = np.concatenate((analog_phase[0,0:4], analog_phase[3,0:4], analog_phase[0,4:8], analog_phase[3,4:8], analog_phase[0,8:12], analog_phase[3,8:12], analog_phase[0,12:16], analog_phase[3,12:16], analog_phase[1,0:4], analog_phase[2,0:4], analog_phase[1,4:8], analog_phase[2,4:8], analog_phase[1,8:12], analog_phase[2,8:12], analog_phase[1,12:16], analog_phase[2,12:16]))
    analog_phase_dict = create_dict(element_map,analog_phase_flatten)
    

    for element in sray_obj.elements.values():
        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))

        # Assign the calculated phase to the element
        element.rx_phase = analog_phase_dict[value]
        sray_obj.latch_rx_settings()  # Latch SPI settings to devices

   
    #print("Analog Phase Dictionary: ", analog_phase_dict)

    # Brute forcing 1x64 analog phase array
    #analog_phase_flatten = np.concatenate((analog_phase[0,0:4], analog_phase[3,0:4], analog_phase[0,4:8], analog_phase[3,4:8], analog_phase[0,8:12], analog_phase[3,8:12], analog_phase[0,12:16], analog_phase[3,12:16], analog_phase[1,0:4], analog_phase[2,0:4], analog_phase[1,4:8], analog_phase[2,4:8], analog_phase[1,8:12], analog_phase[2,8:12], analog_phase[1,12:16], analog_phase[2,12:16]))
    return analog_phase_flatten, analog_phase_dict

def rx_single_channel_data(obj, adc, array, adc_map):
        """
        Captures single channel Rx data on a 1 channel per subarray basis.
        Returns raw ADC codes in a 64x4096 matrix.
        """
        disable_stingray_channel(obj,array)
        rx_data = np.zeros((np.size(array),4096), dtype = complex)  # Allocate memory
        for a in range(np.size(array,1)):
            
            # Enable one reference channel per subarray
            enable_stingray_channel(obj, array[:,a])
            time.sleep(1)
            # Pull data from ADC
            data = np.array(data_capture(adc))
            data = data[:, :np.size(rx_data,1)] # remove data past 4096th column for FFT
            print(get_analog_mag(data))
            print(array[:,a])
            # Initialize temporary array for ADC data
            # This is used to map the ADC data to the correct subarray
            new_data = np.zeros(np.shape(data), dtype = complex)

            for i in range(len(adc_map)):
                # Map data to the correct ADC channels
                new_data[i,:] = data[adc_map[i],:]

          # Map the data to the correct row in the rx_data matrix
                # The row is determined by the index of the subarray
                # rx_data[i,:] = new_data[i,:]
            for index, row in enumerate(array[:,a]):

                # Map the data to the correct row in the rx_data matrix
                # The row is determined by the index of the subarray
                rx_data[row - 1,:] = new_data[index,:]

            # Disable target channels
            disable_stingray_channel(obj, array[:,a])
        return rx_data
 
def get_analog_mag(data):
    """
    get_analog_mag runs an FFT on the data to create a matrix of magnitudes.
    Help: dataADC codes is a 32x4096 matrix of raw ADC codes.
    Returns analog_mag which is a 1x32 row vector of magnitudes in dBFS.
    """
    analog_mag = np.zeros((1, np.size(data,0)))
    
    # print(" shape of analog mag")
    # print(np.shape(analog_mag))
   
    if data.ndim == 1:
        adc_fft_data = fft(data, False, "OneTone")
        analog_mag = adc_fft_data["A:mag_dbfs"]
    else:
        for i in range(np.size(data,0)):
            adc_fft_data = fft(data[i,:], False, "OneTone")
            analog_mag[0,i] = adc_fft_data['A:mag_dbfs']
        

           
    return analog_mag
 
def fft(complex_data, combined_waveforms, tone_type):
    """
    FFT on ADC sample domain waveform data
    """
    qres = 16 # padding out 12 bit ADC to 16 for FFT algorithm
    qres_grow = 18 # bit growth needed to accomadate combining 4 FFTs
    navg = 1
    nfft = 4096
    # Check if bit padding needed
    if combined_waveforms == True:
        qres = qres_grow
        data = complex_data
    elif combined_waveforms == False:
        qres = qres
        data = complex_data
    else:
        raise ValueError('combined_waveforms type unsupported. True or False are acceptable types.')
   
    real_data = data.real.astype(np.int32)
    imag_data = data.imag.astype(np.int32)
    tone_type = tone_type.lower()
    if tone_type == "twotone" and os.path.exists("rx_2tone.json"):
        try:
            with open('rx_2tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    elif tone_type == "onetone" and os.path.exists("rx_1tone.json"):
        try:
            with open('rx_1tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    else:
        raise ValueError('tone_type type unsupported. OneTone or TwoTone are acceptable types.')
    
    # Fourier analysis configuration
    if file.name == "rx_1tone.json":
        key = "fa"
        gn.mgr_remove(key)
        gn.fa_create(key)
        gn.fa_load(file.name, key)
    else:
        raise AttributeError("Have not coded rx_2tone.json for genalyzer yet")
    
    # Do FFT analysis
    window = gn.Window.HANN # window function to apply
    code_fmt = gn.CodeFormat.TWOS_COMPLEMENT # integer data format
    axis_type = gn.FreqAxisType.DC_CENTER # axis type
   
    fft_complex = gn.fft(real_data, imag_data, qres, navg, nfft, window, code_fmt)
    fft_results = gn.fft_analysis(key, fft_complex, nfft, axis_type)

    results = fft_results
    # import matplotlib.pyplot as pl
    # from matplotlib.patches import Rectangle as MPRect

    # fdata = 245.76e6
    
    # freq_axis = gn.freq_axis(nfft, axis_type, fdata, axis_type )

    # fft_db = gn.db(fft_complex)
    # fft_db = gn.fftshift(fft_db)
    # fig = pl.figure(1)
    # fig.clf()
    # pl.plot(freq_axis, fft_db)
    # pl.grid(True)
    # pl.xlim(freq_axis[0], freq_axis[-1])
    # pl.ylim(-140.0, 20.0)
    # annots = gn.fa_annotations(results, axis_type, axis_type )
    # for x, y, label in annots["labels"]:
    #     pl.annotate(label, xy=(x, y), ha="center", va="bottom")
    # for line in annots["lines"]:
    #     pl.axline((line[0], line[1]), (line[2], line[3]), c="pink")
    # for box in annots["ab_boxes"]:
    #     fig.axes[0].add_patch(
    #         MPRect(
    #             (box[0], box[1]),
    #             box[2],
    #             box[3],
    #             ec="lightgray",
    #             fc="gainsboro",
    #             fill=True,
    #             hatch="x",
    #         )
    #     )
    # for box in annots["tone_boxes"]:
    #     fig.axes[0].add_patch(
    #         MPRect(
    #             (box[0], box[1]),
    #             box[2],
    #             box[3],
    #             ec="pink",
    #             fc="pink",
    #             fill=True,
    #             hatch="x",
    #         )
    #     )
    # pl.show()

    return fft_results

def quantize_phase(phase, bits=8):
    """Quantize phase values to specified number of bits"""
    levels = 2**bits
    phase_max = 2*np.pi
    step = phase_max/levels
    return np.round(phase/step)*step

def calc_array_pattern(theta_sweep=(-90, 90), sweep_step=0.5,f_op_GHz=10, elec_steer_angle=[0]):  # Electronic steering angles (az or el)

    # === Constants ===
    from scipy.constants import c
    lambda_op = c / (f_op_GHz * 1e9)      # Wavelength at 11 GHz
    k = 2 * np.pi / lambda_op             # Wavenumber
    d = 0.013635                            # Element spacing = 13.63 mm
    elec_steer_angle = -elec_steer_angle  # Convert to negative for correct direction
    # === Sweep settings
    # Quantized phase settings
    quantize_phased = quantize_phase(np.radians(theta_sweep), bits=8)
    theta_sweep = np.degrees(quantize_phased)

    mechanical_sweep = np.arange(theta_sweep[0], theta_sweep[1]+sweep_step, sweep_step)    # Mechanical sweep angles
    # elec_steer_angles = np.arange(-20, 21, 10)      # Electronic steering angles (az or el)

    # === Array size
    M, N = 8, 8
    x = (np.arange(N) - (N - 1) / 2) * d  # X-coordinates (azimuth direction)
    y = (np.arange(M) - (M - 1) / 2) * d  # Y-coordinates (elevation direction)

    # === Initialize storage
    azim_results = []
    elev_results = []

    steer_rad = np.radians(elec_steer_angle)
    # Electronic steering along X-axis (azimuth)
    steering_weights = np.exp(1j * k * x * np.sin(steer_rad))
    response = []
    for mech_angle in mechanical_sweep:
        mech_rad = np.radians(mech_angle)
        incoming_phase = np.exp(1j * k * x * np.sin(mech_rad))
        pattern = np.dot(steering_weights, incoming_phase)
        response.append(np.abs(pattern))
    response = 20 * np.log10(np.clip(np.array(response) / np.max(response), 1e-10, None))
    azim_results.append(response)
    #Force Column Vector
    azim_results = np.array(azim_results).reshape(-1, 1)

        # === Elevation Beampattern Simulation
    steer_rad = np.radians(elec_steer_angle)
    # Electronic steering along Y-axis (elevation)
    steering_weights = np.exp(1j * k * y * np.sin(steer_rad))
    response = []
    for mech_angle in mechanical_sweep:
        mech_rad = np.radians(mech_angle)
        incoming_phase = np.exp(1j * k * y * np.sin(mech_rad))
        pattern = np.dot(steering_weights, incoming_phase)
        response.append(np.abs(pattern))
    response = 20 * np.log10(np.clip(np.array(response) / np.max(response), 1e-10, None))
    elev_results.append(response)
    #Force Column Vector
    elev_results = np.array(elev_results).reshape(-1, 1)
    elec_steer_angle = -elec_steer_angle  # Convert back to positive for output
    
    return mechanical_sweep, elec_steer_angle, azim_results, elev_results,  # Return the mechanical sweep angles and the pattern for the boresight angle

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
 
conv._rxadc.set_kernel_buffers_count(2) # set buffers as 2 to avoid stale data on AD9081
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

disable_stingray_channel(sray)
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
cal_ant = find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
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
enable_stingray_channel(sray,subarray)

# Take data capture

no_cal_data = np.transpose(np.array(data_capture(conv)))

# Gain cal
disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = rx_gain(sray, conv, subarray, adc_map, sray.element_map)

# print("Gain Dict Size:", gain_dict.shape)
# print("Mag precal: ", mag_pre_cal)
# print("Mag postcal: ", mag_post_cal)



# Phase cal
print("Calibrating Phase... Please wait...")
cal_ant = find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)



#print('peak delay array:',cal_ant)
enable_stingray_channel(sray)
calibrated_data = np.transpose(np.array(data_capture(conv)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
disable_stingray_channel(sray)


plt.ion()   # Turn on interactive mode
fig, axs = plt.subplots(2,1) # Creates a 2x1 grid of subplots

# Test
enable_stingray_channel(sray)

enable_stingray_channel(sray, subarray)
#no_cal_data = np.transpose(np.array(data_capture(conv)))
 
axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100,200])

axs[1].plot(calibrated_data.real)
axs[1].set_title('With Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_xlim([100,200])

# Adjust layout and display
plt.tight_layout()
plt.draw()
plt.pause(0.001) 
plt.show() 

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

maxsweepangle = 180
sweepstep = 1
gimbal_motor = GIMBAL_H


steering_angle = 0 # degrees

print("Before Steering Phase:")
print(sray.all_rx_phases)

sray.steer_rx(azimuth=steering_angle, elevation=0) # Steer to desired angle


for element in sray.elements.values():
    str_channel = str(element)
    value = int(strip_to_last_two_digits(str_channel))

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

steer_data = []
peak_mag = np.zeros(len(gimbal_positions))
print(peak_mag.shape)
for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor,sweepstep)
    time.sleep(0.3)  # Allow time for the gimbal to move to the new position

    steer_data = np.transpose(np.array(data_capture(conv)))
    # Apply Taylor tapering to the received data
    #steer_data = apply_taylor_taper(steer_data, sidelobe_level=-35)
    steer_data = np.array(steer_data).T
    steer_data = cal_data(steer_data, cal_ant)
    steer_data = np.array(steer_data).T

    combined_data = steer_data[:,0] + steer_data[:,1] + steer_data[:,2] + steer_data[:,3]
    peak_mag[i] = get_analog_mag(combined_data)

    converter_0[i] = get_analog_mag(steer_data[:,0])
    converter_1[i] = get_analog_mag(steer_data[:,1])
    converter_2[i] = get_analog_mag(steer_data[:,2])
    converter_3[i] = get_analog_mag(steer_data[:,3])
    
print(peak_mag.shape)    
mbx.gotoZERO()


# peak_mag = apply_taylor_taper(peak_mag.reshape(-1, 1), sidelobe_level=-35).flatten()  # Apply Taylor tapering to peak magnitudes
# Calculate peak FFT magnitude for each steering angle
norm_peak_mag = peak_mag - np.max(peak_mag)  # Normalize the peak magnitudes    
    

# Define the corresponding angles (assuming gimbal_positions is 0 to 80, map to -40 to 40)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))


# Plot peak magnitude vs mechanical azimuth angle with cosine rolloff
th = np.linspace(-90, 90, 1000)  # degrees
th_rad = np.deg2rad(th)

# cosTheta^1
cosTh1p0 = 20 * np.log10(np.abs(np.cos(th_rad)**1.0)) + np.max(peak_mag)
# cosTheta^1.2
cosTh1p2 = 20 * np.log10(np.abs(np.cos(th_rad)**1.2)) + np.max(peak_mag)
# cosTheta^1.5
cosTh1p5 = 20 * np.log10(np.abs(np.cos(th_rad)**1.5)) + np.max(peak_mag)
# cosTheta^1.7
cosTh1p7 = 20 * np.log10(np.abs(np.cos(th_rad)**1.7)) + np.max(peak_mag)
# cosTheta^2.0
cosTh2p0 = 20 * np.log10(np.abs(np.cos(th_rad)**2.0)) + np.max(peak_mag)

plt.figure(figsize=(10, 6))
plt.plot(th, cosTh1p0, label='n=1.0')
plt.plot(th, cosTh1p2, label='n=1.2')
plt.plot(th, cosTh1p5, label='n=1.5')
plt.plot(th, cosTh1p7, label='n=1.7')
plt.plot(th, cosTh2p0, label='n=2.0')
plt.title('Element Pattern Models (cos^n θ)')
plt.xlabel('Angle (degrees)')
plt.ylabel('Relative Power (dB)')
plt.grid(True)
plt.legend()
plt.ylim(-50, 0)

plt.plot(angles, peak_mag)
plt.title("Peak FFT Magnitude vs Mechanical Azimuth Angle - Combined Data")
plt.xlabel("Azimuth Angle (degrees)")
plt.ylabel("Peak FFT Magnitude (dBFs)")
plt.grid(True)
plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
plt.draw()
plt.pause(0.001) 


# Calculate and plot
mechanical_sweep, elec_steer_angle, azim_results, elev_results, = calc_array_pattern(elec_steer_angle=steering_angle)

# === Plot Azimuth Cuts
plt.figure(figsize=(10, 6))
# Plot theoretical results
plt.plot(mechanical_sweep, azim_results, label=f'Theoretical Pattern',color='red')
# Plot measured results
plt.plot(angles, norm_peak_mag,linestyle='dotted', label='Measured Data', color='blue',markersize=9)
plt.title(f'Azimuth Cuts (X-Axis Steering at {elec_steer_angle}°)')
plt.xlabel('Mechanical Azimuth Angle (degrees)')
plt.ylabel('Normalized Gain (dB)')
plt.ylim(-60, 0)
plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
plt.grid(True)
plt.legend(title='Electronic Steer')
plt.tight_layout()
plt.draw()
plt.pause(0.001) 

""""
# Plots For Each Beamformer Card ###
#                                ###
#                                ###


fig, axs = plt.subplots(2,2) # Creates a 2x1 grid of subplots

converter0norm = converter_0 - np.max(converter_0) 
converter1norm = converter_1 - np.max(converter_1)
converter2norm = converter_2 - np.max(converter_2)
converter3norm = converter_3 - np.max(converter_3)


# Plot
axs[0,0].plot(angles, converter0norm)
axs[0,0].set_title("Peak FFT Magnitude vs Mechanical Azimuth Angle - Tile 0")
axs[0,0].set_xlabel("Azimuth Angle (degrees)")
axs[0,0].set_ylabel("Peak FFT Magnitude (dBi)")
axs[0,0].grid(True)
axs[0,0].set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])


# Plot
axs[0,1].plot(angles, converter1norm)
axs[0,1].set_title("Peak FFT Magnitude vs Mechanical Azimuth Angle - Tile 1")
axs[0,1].set_xlabel("Azimuth Angle (degrees)")
axs[0,1].set_ylabel("Peak FFT Magnitude (dBi)")
axs[0,1].grid(True)
axs[0,1].set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])



# Plot
axs[1,0].plot(angles, converter2norm)
axs[1,0].set_title("Peak FFT Magnitude vs Mechanical Azimuth Angle - Tile 2")
axs[1,0].set_xlabel("Azimuth Angle (degrees)")
axs[1,0].set_ylabel("Peak FFT Magnitude (dBi)")
axs[1,0].grid(True)
axs[1,0].set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])



# Plot
axs[1,1].plot(angles, converter3norm)
axs[1,1].set_title("Peak FFT Magnitude vs Mechanical Azimuth Angle - Tile 3")
axs[1,1].set_xlabel("Azimuth Angle (degrees)")
axs[1,1].set_ylabel("Peak FFT Magnitude (dBi)")
axs[1,1].grid(True)
axs[1,1].set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])

plt.tight_layout()
plt.draw()
plt.pause(0.001) 


#fig, axs = plt.subplots(1,1) # Creates a 2x1 grid of subplots

# Phase alignment test after gimbal sweep

## Take data capture of each ADC post gimbal movement
enable_stingray_channel(sray)
post_gimbal_sweep_data = np.transpose(np.array(data_capture(conv)))
post_gimbal_sweep_data = np.array(post_gimbal_sweep_data).T
post_gimbal_sweep_data = cal_data(post_gimbal_sweep_data, cal_ant)
post_gimbal_sweep_data = np.array(post_gimbal_sweep_data).T




# Plot
plt.figure()
plt.plot(post_gimbal_sweep_data.real)
plt.title('With Calibration After Returning to Zero Position')
plt.xlabel("Index")
plt.ylabel("Value")
plt.grid(visible=True)
plt.xlim([100,200])
plt.draw()
plt.pause(0.001) 
"""

# Show plot

plt.show(block=True) 

# Create a dictionary with the data you want to export
matlab_data = {
    'mechanical_angles': angles,
    'measured_pattern': norm_peak_mag,
    'theoretical_pattern': azim_results.flatten(),
    'steering_angle': steering_angle,
    'cal_antenna': cal_ant,
    'converter_0': converter_0,
    'converter_1': converter_1,
    'converter_2': converter_2,
    'converter_3': converter_3
}

# Save to .mat file
savemat('beamforming_data.mat', matlab_data)