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

BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB0"



def data_capture(adc):
    adc.rx_destroy_buffer() # clear previous data
    for i in range(2):
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    
    return data

def get_analog_mag(data):
    """
    get_analog_mag runs an FFT on the data to create a matrix of magnitudes.
    Help: dataADC codes is a 32x4096 matrix of raw ADC codes.
    Returns analog_mag which is a 1x32 row vector of magnitudes in dBFS.
    """
    analog_mag = np.zeros((1, np.size(data,0)))
    
    print(" shape of analog mag")
    print(np.shape(analog_mag))
   
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


SELF_BIASED_LNAs = True
ARRAY_MODE = "rx" # start rx cals first
#print("Turn on RF Source...")
#input('Press Enter to continue...')
url = "ip:192.168.0.1"
print("Connecting to", url ,"...")

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


mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()
# Define sweep parameters
mechanicalsweepWidth = np.arange(-80, 85, 5)
elecsteerangleazim = np.arange(-20, 21, 10)
elecsteerangleelev = np.arange(-20, 21, 10)
freq = 10e9  # Frequency in Hz



GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

gimbal_motor = GIMBAL_H

sweepangles = np.arange(-90, 91, 1)
mbx.move(gimbal_motor, 1 )

gimbal_positions = np.arange(0, 81, 1)  # Define gimbal positions from -90 to 90 degrees
mbx.move(gimbal_motor,-40)

steer_data = []
peak_mag = np.zeros(len(gimbal_positions))
print(peak_mag.shape)
for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor,1)
    # ## Take data capture
    steer_data = np.transpose(np.array(data_capture(conv)))
    combined_data = steer_data[:,0] + steer_data[:,1] + steer_data[:,2] + steer_data[:,3]
    peak_mag[i] = get_analog_mag(combined_data)
print(peak_mag.shape)    
mbx.gotoZERO()

# Calculate peak FFT magnitude for each steering angle
    
    

# Define the corresponding angles (assuming gimbal_positions is 0 to 80, map to -40 to 40)
angles = np.linspace(-40, 40, len(gimbal_positions))

# Plot
plt.figure()
plt.plot(angles, peak_mag)
plt.title("Peak FFT Magnitude vs Mechanical Azimuth Angle")
plt.xlabel("Azimuth Angle (degrees)")
plt.ylabel("Peak FFT Magnitude")
plt.grid(True)
plt.xlim([-40, 40])
plt.show()