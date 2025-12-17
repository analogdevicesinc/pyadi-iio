import adi
import pyvisa
from pyvisa import constants
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import N9000A_Driver as N9000A
import E8267D_Driver as E8267D
import N6705B_Driver as N6705B
import E36233A_Driver as E36233A
import paramiko
import MantaRay as mr
import math
import sys
import mbx_functions as mbx
import subprocess
import os
import sys


talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 4
    ])



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


## Set attenuation to 1, gain to max, and phase to 0 for all elements ##
for element in dev.elements.values():
    """
    Iterate through each element in the Stingray object
    Convert the element to a string and extract the last two digits
    This is used to map the element to its corresponding gain and attenuation values
    in the dictionaries created above
    """
    str_channel = str(element)
    print(element)
    value = int(mr.strip_to_last_two_digits(str_channel))

    # element.tx_attenuator = atten_dict[value]
    element.tx_attenuator = 1
    time.sleep(0.1)
    element.tx_gain = 127
    element.tx_phase = 0

    dev.latch_tx_settings() # Latch SPI settings to devices

    
## Set TR Source, Mode, and Bias DAC Mode ##
for device in dev.devices.values():
    device.tr_source = "external"
for device in dev.devices.values():    
    # device.mode = "rx"
    device.bias_dac_mode = "on"



## Set PA Bias ON/OFF to -4.8V for all channels ##
tries = 10
for device in dev.devices.values():
    # device.mode = "rx"
    device.bias_dac_mode = "on"

    for channel in device.channels:
        channel.pa_bias_on = -4.8
        if round(channel.pa_bias_on,1) != -4.8:
            found = False
            for _ in range(tries):
                if round(channel.pa_bias_on,1) != -4.8:
                    pass
                else:
                    found = True
                    break
            if not found:
                print(f"Not set properly: {channel.pa_bias_on=}")
                print(f"Element number {channel}")
        
        channel.pa_bias_off = -4.8
        if round(channel.pa_bias_off,1) != -4.8:
            found = False
            for _ in range(tries):
                if round(channel.pa_bias_off,1) != -4.8:
                    pass
                else:
                    found = True
                    break
            if not found:
                print(f"Not set properly: {channel.pa_bias_off=}")
                print(f"Element number {channel}")
        dev.latch_tx_settings()


## Set TR Source to external and bias_dac_mode to toggle ##
for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"

    
dev.latch_tx_settings()