
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

## Set up VISA for external instruments ##
rm = pyvisa.ResourceManager()

CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
SpecAn = N9000A.N9000A(rm, CXA)
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

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

mr.disable_pa_bias_channel(dev)
print("Setting Phases back to 0")
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
    element.tx_phase = 0
    dev.latch_tx_settings() #

## Element 3 is in subarray 1
sub1_ref_channel = 3

sub2_ref_channel = 35

sub3_ref_channel = 39

sub4_ref_channel = 7

ref_channels = [3, 35, 39, 7]
mr.disable_pa_bias_channel(dev)
## Enable master reference
mr.enable_pa_bias_channel(dev, sub1_ref_channel)

dac_phase_offsets = []

for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    if value in ref_channels:
        if value != sub1_ref_channel:
            detect = []
            print(f"Element: {value}")
            mr.enable_pa_bias_channel(dev, [value])


            for j in range (181):

                element.tx_phase = j
                print('Phase: ', element.tx_phase)
                dev.latch_tx_settings()
                tone_0 = SpecAn.get_marker_power(marker=1)
                detect.append(tone_0)

            mr.disable_pa_bias_channel(dev, [value])
            min_phase = detect.index(min(detect))
            print(f'Null power at {min_phase} deg')
            print(f'Setting {element} calibrated phase')
            element.tx_phase = 0
            dac_phase_offsets.append(min_phase + 180)
            dev.latch_tx_settings()    
        else:
            pass

    else:
        pass



mr.disable_pa_bias_channel(dev, sub1_ref_channel)
print('DAC Null Power Phase Calibration Complete')
print(dac_phase_offsets)
print(np.array(dac_phase_offsets) % 360)
print(np.array(dac_phase_offsets) % 180)


