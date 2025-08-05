import time
import importlib
from calibration import *

import genalyzer as gn
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import adar_functions
import re
import json
import os

url = "ip:192.168.0.1" 


sray = adi.adar1000_array(
    uri = url,

    chip_ids = ["adar1000_csb_0_2_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_4", "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_1_1",
                "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
                "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
   
    device_map = [[1, 5, 2, 6], [3, 7, 4, 8],[9, 13, 10, 14], [11, 15, 12, 16]],

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


def enable_stingray_channel(obj, elements=None, man_input=False):
    """
    Enables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn on (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    if man_input == False:
        elements = np.array(elements).flatten()


    for device in obj.devices.values():
        for channel in device.channels:

            str_channel = str(channel)
            value = int(strip_to_last_two_digits(str_channel))

            # Check if the channel is in the list of elements to disable
            # If it is, disable the channel
            for elem in elements:
                if elem == value:
                    # print("Turning on element:",elem)
                    channel.rx_enable = True
 
enable_stingray_channel(sray, elements=list(range(1,65)), man_input=True)

# for element in sray.elements.values():
#     element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
#     element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
#     element.rx_phase = 0 # Set all phases to 0
# sray.latch_rx_settings() # Latch SPI settings to devices


disable_stingray_channel(sray, elements=list(range(1,65)), man_input=False)



