# Manta Ray 64 Element Electronic Steering Array Calibration and Sweep
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import time
import importlib
import genalyzer as gn
import adi
# from adi.sshfs import sshfs
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
import paramiko




import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np
import paramiko



BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB1"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()
exit()
SELF_BIASED_LNAs = True
ARRAY_MODE = "tx" # start rx cals first
#print("Turn on RF Source...")
#input('Press Enter to continue...')
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

 
# url = "local:" if len(sys.argv) == 1 else sys.argv[1]
# ssh = sshfs(address=url, username="root", password="analog")
 

# # Setup Talise RX, TDDN Engine & ADAR1000

 
# tddn = adi.tddn(uri = url)
 

# fs_RxIQ = 245.76e6;  #I/Q Data Rate in MSPS

# # Startup and connect TDDN
# tddn.enable = False
# tddn.startup_delay_ms = 0
# # Configure top level engine
# samplesPerFrame = 2**12
# frame_length_ms = samplesPerFrame/fs_RxIQ*1000
# tddn.frame_length_ms = frame_length_ms
# # Configure component channels
# on_time = 0
# off_time = frame_length_ms - 0.1
# # Setup TDDN Channel for CW mode
# tddn_channels = {
#     "TX_OFFLOAD_SYNC": 0,
#     "RX_OFFLOAD_SYNC": 1,
#     "TDD_ENABLE": 2,
#     "RX_MXFE_EN": 3,
#     # "TX_MXFE_EN": 4,
#     # "TX_STINGRAY_EN": 5
# }
# # Assign channel properties for CW
# for key, value in tddn_channels.items():
#     if value == 0 or value == 1:
#         tddn.channel[value].on_raw = 0
#         tddn.channel[value].off_raw = 0
#         tddn.channel[value].on_ms = 0
#         tddn.channel[value].off_ms = 0
#         tddn.channel[value].polarity = True
#         tddn.channel[value].enable = True
#     elif value == 2 or value == 5:
#         tddn.channel[value].on_raw = 0
#         tddn.channel[value].off_raw = 0
#         tddn.channel[value].on_ms = 0
#         tddn.channel[value].off_ms = 0
#         tddn.channel[value].polarity = False
#         tddn.channel[value].enable = True
#     else:
#         tddn.channel[value].on_raw = 0
#         tddn.channel[value].off_raw = 10
#         tddn.channel[value].polarity = True
#         tddn.channel[value].enable = True
# tddn.enable = True # Fire up TDD engine
# tddn.sync_internal = True # software enable TDD mode
# # Setup Stingray for RX mode
# # tddn.sync_soft = True

# conv = adi.adrv9009_zu11eg(uri = url)
 
# conv._rxadc.set_kernel_buffers_count(1)
# conv.rx_main_nco_frequencies = [450000000] * 4
# conv.rx_main_nco_phases = [0] * 4
# conv.rx_channel_nco_frequencies = [0] * 4
# conv.rx_channel_nco_phases = [0] * 4
# conv.rx_enabled_channels = [0, 1, 2, 3]
# conv.rx_nyquist_zone     = ["odd"] * 4
# conv.rx_buffer_size = 2 ** 12
# conv.dds_phases = []
# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# Force set the Data Offload Tx to run in cyclic mode
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(talise_ip, username="root", password="analog")
print(f"Run cmd: busybox devmem 0x9c460088 32 0x0")
stdin, stdout, stderr = ssh.exec_command(f"busybox devmem 0x9c460088 32 0x0")
stdout_str = stdout.read().decode()
stderr_str = stderr.read().decode()
print(stdout_str)
print(stderr_str)
stdout.close()
stderr.close()
ssh.close()


# USER CONFIGURABLE PARAMETERS
# Configure TX properties
sdr.tx_enabled_channels = [0, 1, 2, 3]
# sdr.trx_lo = 4500000000            # [29, 30, 31, 32],
#                 ],
#     device_element_map={
#                 1: 	[4, 8, 7, 3],
#                 2: 	[2, 6, 5, 1],
#                 3: 	[13, 9, 10, 14],
#                 4: 	[15, 11, 12, 16],
#                 # 5: 	[20, 24, 23, 19],
#                 # 6: 	[18, 22, 21, 17],
#                 # 7: 	[29, 25, 26, 30],
#                 # 8: 	[31, 27, 28, 32],
#     },
# )
# sdr.trx_lo_chip_b = 4500000000
# sdr.trx_lo = 1000000000
sdr.tx_hardwaregain_chan0 = -20
sdr.tx_hardwaregain_chan1 = -20
sdr.tx_hardwaregain_chan0_chip_b= -20
sdr.tx_hardwaregain_chan1_chip_b = -20
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.gain_control_mode_chan0_chip_b = "manual"
sdr.gain_control_mode_chan1_chip_b = "manual"
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"
sdr.gain_control_mode_chan0_chip_b = "slow_attack"
sdr.gain_control_mode_chan1_chip_b = "slow_attack"

# Number of frame pulses to plot in the pulse train
# (will be used to calculate the RX buffer size)
frame_pulses_to_plot = 5

# Frame and pulse timing (in milliseconds)
frame_length_ms = 0.04 # 40 us
# sine data for 20 us pulse than 20 us of zero data
tx_pulse_start_ms = 0.00001 # 10 ns
tx_pulse_stop_ms = 0.04 # 20 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
tx_pulse_duration_ms = tx_pulse_stop_ms - tx_pulse_start_ms
tx_pulse_duration_seconds = tx_pulse_duration_ms * 1e-3
tx_pulse_samples = int(fs * tx_pulse_duration_seconds)
tx_start_sample = int(fs * tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
i = np.zeros(N)
q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(tx_start_sample, min(tx_start_sample + tx_pulse_samples, N)):
    t_sample = n * ts
    i[n] = np.cos(2 * np.pi * fc * t_sample) * 0.1
    q[n] = np.sin(2 * np.pi * fc * t_sample) * 0.1

data = i + 1j * q
sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
iq_real = np.int16(np.real(data) * scale_factor)
iq_imag = np.int16(np.imag(data) * scale_factor)
iq = iq_real + 1j * iq_imag

# Configure RX parameters
sdr.rx_enabled_channels = [0, 1, 2, 3]

# Calculate RX buffer size to match TX duration
rx_fs = int(sdr.rx_sample_rate)

# Match RX buffer duration to TX duration
desired_rx_duration = frame_pulses_to_plot * len(iq) / fs * 1000  # ms
rx_buffer_samples = int(rx_fs * (desired_rx_duration * 1e-3))
sdr.rx_buffer_size = rx_buffer_samples

# Create time vector for plotting
rx_ts = 1 / float(rx_fs)
rx_t = np.arange(0, rx_buffer_samples * rx_ts, rx_ts)

# Create pulse train for the entire RX buffer duration
pulse_train = np.zeros(rx_buffer_samples)

# Calculate samples per frame and pulse
samples_per_frame = int(frame_length_ms * 1e-3 / rx_ts)
pulse_start_offset = int(tx_pulse_start_ms * 1e-3 / rx_ts)
pulse_stop_offset = int(tx_pulse_stop_ms * 1e-3 / rx_ts)

num_frames = len(rx_t) // samples_per_frame

for frame in range(num_frames):
    frame_start = frame * samples_per_frame
    pulse_start = frame_start + pulse_start_offset
    pulse_stop = frame_start + pulse_stop_offset
    pulse_train[pulse_start:pulse_stop] = 1

# TDD signal channels
TDD_TX_OFFLOAD_SYNC = 0
TDD_RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2
TDD_ADRV9009_RX_EN = 3
TDD_ADRV9009_TX_EN = 4

#Configure TDD engine
tddn.enable = 0

# tddn.burst_count          = 0 # continuous mode, period repetead forever
# tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms

for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN]:
    tddn.channel[chan].on_ms   = 0
    tddn.channel[chan].off_ms  = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable   = 1

for chan in [TDD_TX_OFFLOAD_SYNC,TDD_RX_OFFLOAD_SYNC]:
    tddn.channel[chan].on_raw   = 0
    tddn.channel[chan].off_raw  = 10 # 10 samples at 250 MHz = 40 ns pulse width
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable   = 1

tddn.enable = 1

tdd_tx_offload_frame_length_ms = frame_length_ms
tdd_tx_offload_pulse_start_ms = 0.00001 # 10 ns

# off_raw is in samples, so convert to time for offset calculation
off_raw_samples = tddn.channel[TDD_TX_OFFLOAD_SYNC].off_raw

# Create pulse train for the entire RX buffer duration
tdd_tx_offload_pulse_train = np.zeros(rx_buffer_samples)

# Calculate samples per frame and pulse
tdd_tx_offload_samples_per_frame = int(frame_length_ms * 1e-3 / rx_ts)
tdd_tx_offload_pulse_start_offset = int(tdd_tx_offload_pulse_start_ms * 1e-3 / rx_ts)
# Pulse stays high for off_raw_samples
tdd_tx_offload_pulse_stop_offset = tdd_tx_offload_pulse_start_offset + off_raw_samples

# Only plot as many pulses as requested
for frame in range(frame_pulses_to_plot):
    tdd_tx_offload_frame_start = frame * tdd_tx_offload_samples_per_frame
    tdd_tx_offload_pulse_start = tdd_tx_offload_frame_start + tdd_tx_offload_pulse_start_offset
    tdd_tx_offload_pulse_stop = tdd_tx_offload_frame_start + tdd_tx_offload_pulse_stop_offset
    tdd_tx_offload_pulse_train[tdd_tx_offload_pulse_start:tdd_tx_offload_pulse_stop] = 1

# Send TX data
sdr.tx_destroy_buffer()
# When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
sdr.tx([iq, iq, iq, iq])

# Trigger TDD synchronization
tddn.sync_soft  = 1

# Force set the Data Offload Tx to run in cyclic mode
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(talise_ip, username="root", password="analog")
print(f"Run cmd: busybox devmem 0x9c460088 32 0x0")
stdin, stdout, stderr = ssh.exec_command(f"busybox devmem 0x9c460088 32 0x0")
stdout_str = stdout.read().decode()
stderr_str = stderr.read().decode()
print(stdout_str)
print(stderr_str)
stdout.close()
stderr.close()
ssh.close()

tddn.sync_soft  = 1



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
# Setup ADXUD1AEBZ and ADF4371
ctx = sdr._ctrl.ctx
xud = ctx.find_device("xud_control")
stingray_control_spi_0 = ctx.find_device("stingray0_control") 
PA_on_spi0 = stingray_control_spi_0.find_channel("voltage0", True)
stingray_control_spi_1 = ctx.find_device("stingray1_control") 
PA_on_spi1 = stingray_control_spi_1.find_channel("voltage0", True)


# Find channel attribute for TX & RX
txrx1 = xud.find_channel("voltage1", True)
txrx2 = xud.find_channel("voltage2", True)
txrx3 = xud.find_channel("voltage3", True)
txrx4 = xud.find_channel("voltage4", True)
rxgainmode = xud.find_channel("voltage0", True)


 
# 0 for rx, 1 for tx
txrx1.attrs["raw"].value = "1" # Subarray 4
txrx2.attrs["raw"].value = "1" # Subarray 3
txrx3.attrs["raw"].value = "1" # Subarray 1
txrx4.attrs["raw"].value = "1" # Subarray 2
rxgainmode.attrs["raw"].value = "1"

mr.disable_stingray_channel(sray)

if ARRAY_MODE == "rx":
    print("ARRAY_MODE =",ARRAY_MODE,"Setting all devices to rx mode")
    for element in sray.elements.values():
        element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
        element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
        element.rx_phase = 0 # Set all phases to 0
    sray.latch_rx_settings() # Latch SPI settings to devices

if ARRAY_MODE == "tx":

    print("Initializing BFC Tile")
    sray.initialize_devices(-4.8, -4.8, -4.8, -4.8)
    for device in sray.devices.values():
        device.mode = "rx"
        device.bias_dac_mode = "on"
        for channel in device.channels:
            # Default channel enable
            channel.rx_enable = True
    print("Initialized BFC Tile")

    print("ARRAY_MODE =",ARRAY_MODE,"Setting ADAR1000s to external TR source and setting bias DAC mode to toggle")
    for device in sray.devices.values():
         device.tr_source = "spi" # internal or external
         device.bias_dac_mode = "toggle"

    print("ARRAY_MODE =",ARRAY_MODE,"Setting ADAR1000s to bias external TR PAs at -2V when TX enabled and -4V when TX disabled")
    for element in sray.elements.values():
        element.pa_bias_on = -2
        element.pa_bias_off = -4.5
    sray.latch_tx_settings() # Latch SPI settings to devices
    

    user_input = input("Set PA to 16V, Press Enter to continue, or 'q' to quit: ")
    if user_input.lower() == 'q':
        print("Quitting...")
        sys.exit(0)

    user_input = input("Turning on Stingray Channel 1 Press Enter to continue, or 'q' then Enter to quit: ")
    if user_input.lower() == 'q':
        print("Quitting...")
        sys.exit(0)
    mr.enable_stingray_channel(sray, elements=[1])

    print("ARRAY_MODE =",ARRAY_MODE,"Setting ADAR1000s to external TR source and setting bias DAC mode to toggle")
    for device in sray.devices.values():
         device.tr_source = "external" # 

    user_input = input("Turning on main PA_ON Press Enter to continue, or 'q' then Enter to quit: ")
    if user_input.lower() == 'q':
        print("Quitting...")
        sys.exit(0)
    PA_on_spi0.attrs["raw"].value = "1"
    PA_on_spi1.attrs["raw"].value = "1"


print(True)
