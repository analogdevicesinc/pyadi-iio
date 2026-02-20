# Manta Ray 64 Element Electronic Steering Array Calibration and Sweep
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import os
os.environ['QT_QPA_PLATFORM'] = 'wayland'

import matplotlib
import time
import importlib
from datetime import datetime
import genalyzer as gn
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import re
import json
import pandas as pd
from scipy.special import factorial
from scipy.io import savemat
import sys
from MantaRayTx_Cal import MantaRay as mr
import paramiko
import pyvisa
import genalyzer as gn

# Import from Drivers folder (subfolder relative to this file)
from Drivers import N9000A_Driver as N9000A
from Drivers import E8267D_Driver as E8267D
from Drivers import N6705B_Driver as N6705B
from Drivers import E36233A_Driver as E36233A

# Import from Millibox folder (subfolder relative to this file)
from Millibox import mbx_functions as mbx

# ----------------------------
# USER PLOT OPTIONS
# ----------------------------
SAVE_SEPARATE_AZ_EL_PNGS = True   # keep your separate AZ and EL Σ/Δ pngs
SAVE_COMBINED_4TRACE_PNG = True   # new: AZ+EL overlay 4-trace plot
NORMALIZE_FOR_ASYMMETRY  = False  # if True, each trace is shifted so its peak is 0 dB (shape comparison)

## Gimbal connection parameters ##
BAUDRATE   = 57600
DEVICENAME = "/dev/ttyUSB0"
mbx.connect(DEVICENAME, BAUDRATE)

## Connect to power supplies ##
## Set up VISA for external instruments ##
rm = pyvisa.ResourceManager()

## Keysight N6705B Power Supply (modular) for Manta Ray Rails ##
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)

NUM_REPEATS = 1

## Setup SSH conection into Talise SOM for control ##
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")

SELF_BIASED_LNAs = True
ARRAY_MODE = "rx"
url = "ip:192.168.1.1"
print("Connecting to", url, "...")

ssh = sshfs(address=url, username="root", password="analog")

# Setup Talise RX, TDDN Engine & ADAR1000
tddn = adi.tddn(uri=url)

fs_RxIQ = 245.76e6  # I/Q Data Rate in MSPS
conv = adi.adrv9009_zu11eg(uri=url)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12
conv.dds_phases = []

## Define Subarrays, Reference Channels, and ADC maps ##
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],  # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],  # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],  # subarray 4
])
subarray_ref = np.array([1, 33, 37, 5])
adc_map = np.array([0, 1, 2, 3])  # ADC map to subarray
adc_ref = 0  # ADC reference channel (indexed at 0)

## Setup ADAR1000 Array ##
sray = adi.adar1000_array(
    uri=url,

    chip_ids=[
        "adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",

        "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"
    ],

    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],

    element_map=np.array([
        [1, 9, 17, 25, 33, 41, 49, 57],
        [2, 10, 18, 26, 34, 42, 50, 58],
        [3, 11, 19, 27, 35, 43, 51, 59],
        [4, 12, 20, 28, 36, 44, 52, 60],

        [5, 13, 21, 29, 37, 45, 53, 61],
        [6, 14, 22, 30, 38, 46, 54, 62],
        [7, 15, 23, 31, 39, 47, 55, 63],
        [8, 16, 24, 32, 40, 48, 56, 64]
    ]),

    device_element_map={
        1: [9, 10, 2, 1],      3: [41, 42, 34, 33],
        2: [25, 26, 18, 17],   4: [57, 58, 50, 49],
        5: [4, 3, 11, 12],     7: [36, 35, 43, 44],
        6: [20, 19, 27, 28],   8: [52, 51, 59, 60],

        9: [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],  12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],  16: [56, 55, 63, 64],
    },
)

# Define delay phases for phase calibration
delay_phases = np.arange(-180, 181, 1)  # sweep phase from -180 to 180 in 1 degree steps.

# Disable all channels initially
mr.disable_stingray_channel(sray)
sray.latch_rx_settings()

d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]  # analog target channels
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0], -1))  # matrix of targets wrt reference

# Set RX array to desired mode and set ADAR1000s to max gain and 0 phase
if ARRAY_MODE == "rx":
    print("ARRAY_MODE =", ARRAY_MODE, "Setting all devices to rx mode")
    for element in sray.elements.values():
        element.rx_attenuator = 0  # 1: attenuation on; 0: off
        element.rx_gain = 127       # 127: highest gain
        element.rx_phase = 0        # phases to 0
    sray.latch_rx_settings()  # latch SPI settings

# Broadside steer to start
sray.steer_rx(azimuth=0, elevation=0)

# Setup ADXUD1AEBZ
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)

cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"

# Enable subarray reference
mr.enable_stingray_channel(sray, subarray)

# Take data capture
no_cal_data = np.transpose(np.array(mr.data_capture(conv)))

# Gain cal
mr.disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(sray, conv, subarray, adc_map, sray.element_map)

# Phase cal
print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(
    sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant
)

# Take calibrated data capture
mr.enable_stingray_channel(sray)
calibrated_data = np.transpose(np.array(mr.data_capture(conv)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = mr.cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
mr.disable_stingray_channel(sray)

## Plot results ##
plt.ion()
fig, axs = plt.subplots(2, 1)

axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100, 600])
axs[1].set_ylim([-28000, 28000])

axs[1].plot(calibrated_data.real)
axs[1].set_title('With Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_ylim([-28000, 28000])
axs[1].set_xlim([100, 600])

plt.savefig('MantaRay_64Element_Electronic_Steering_Array_Calibration.png')
plt.tight_layout()
plt.draw()
plt.pause(0.001)
plt.show()

steering_angle = 0  # degrees

print("Before Steering Phase:")
print(sray.all_rx_phases)

sray.steer_rx(azimuth=steering_angle, elevation=0)

for element in sray.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360

sray.latch_rx_settings()

print("After Steering Phase:")
print(sray.all_rx_phases)

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

sig_gen_freq_GHz = 10
steering_angle = 0   # degrees
maxsweepangle = 120  # degrees
sweepstep = 1

gimbal_motor = GIMBAL_H
gimbal_positions = np.arange(0, (maxsweepangle + 1), sweepstep)
angles = np.linspace(-(maxsweepangle / 2), (maxsweepangle / 2), len(gimbal_positions))

mbx.move(gimbal_motor, -(maxsweepangle / 2))

single_element_sweep = []
steer_data = []
mag_single_sweep = []
peak_mag = np.zeros(len(gimbal_positions))
print(peak_mag.shape)

# Define steering angles to test
steering_angles = [0]

# Output folder setup
base_out_dir = "/home/snuc/Desktop/rx_subarray_plots_feb13"
os.makedirs(base_out_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("\n" + "=" * 70)
print("STARTING COMBINED RX BEAM PATTERN TEST FOR ALL SUBARRAYS")
print("=" * 70)

# Calculate and plot (unchanged call)
mechanical_sweep, elec_steer_angle, azim_results, elev_results = mr.calc_array_pattern(
    elec_steer_angle=steering_angle, f_op_GHz=sig_gen_freq_GHz
)

# Initialize arrays for both azimuth and elevation
peak_mags_az = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_az_delta = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_el = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_el_delta = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}

# NEW: store per-run magnitudes so we can compute true mean at end
all_powers_64_delta = [[] for _ in range(NUM_REPEATS)]
all_powers_64_el_delta = [[] for _ in range(NUM_REPEATS)]

# Initialize storage for all IQ data and metadata
all_iq_data_64 = [[] for _ in range(NUM_REPEATS)]
all_gimbal_angles_64 = [[] for _ in range(NUM_REPEATS)]
all_steering_angles_64 = [[] for _ in range(NUM_REPEATS)]
all_powers_64 = [[] for _ in range(NUM_REPEATS)]
all_sum_iq_64 = [[] for _ in range(NUM_REPEATS)]
all_delta_iq_64 = [[] for _ in range(NUM_REPEATS)]

# Elevation storage
all_iq_data_64_el = [[] for _ in range(NUM_REPEATS)]
all_sum_iq_64_el = [[] for _ in range(NUM_REPEATS)]
all_delta_iq_64_el = [[] for _ in range(NUM_REPEATS)]
all_gimbal_angles_64_el = [[] for _ in range(NUM_REPEATS)]
all_steering_angles_64_el = [[] for _ in range(NUM_REPEATS)]
all_powers_64_el = [[] for _ in range(NUM_REPEATS)]

# =====================================================
# === AZIMUTH LIVE PLOT (Σ and Δ)
# =====================================================
print("Starting Azimuth Sweep...")
gimbal_motor = GIMBAL_H
mbx.gotoZERO()
mbx.move(gimbal_motor, -(maxsweepangle / 2))

plt.ion()
fig_full_array, ax_full_array = plt.subplots(figsize=(14, 8))
mng = fig_full_array.canvas.manager
try:
    mng.window.showMaximized()
except:
    pass

line_full_array, = ax_full_array.plot([], [], linestyle='dotted', marker='o', markersize=6,
                                      linewidth=2, color='tab:blue', label='Az Σ (Sum)')
line_delta_array, = ax_full_array.plot([], [], color="tab:orange", linestyle="--",
                                       linewidth=2, marker='s', markersize=5, label="Az Δ (Delta)")

ax_full_array.set_xlabel("Mechanical Azimuth Angle (degrees)", fontsize=14)
ax_full_array.set_ylabel("Combined RF Input Power (dBm)", fontsize=14)
ax_full_array.set_title(f"RX Azimuth Pattern – Σ / Δ (Live) @ {sig_gen_freq_GHz} GHz",
                        fontsize=16, fontweight='bold')
ax_full_array.set_xlim([-(maxsweepangle / 2), (maxsweepangle / 2)])
ax_full_array.grid(True, alpha=0.3)
ax_full_array.legend(fontsize=12, loc='best')

# ----------------------------
# MAIN REPEAT LOOP
# ----------------------------
for run_idx in range(NUM_REPEATS):
    print(f"\n===== STARTING RUN {run_idx + 1}/{NUM_REPEATS} =====")

    # --- Reset AZ gimbal to start position for this run ---
    gimbal_motor = GIMBAL_H
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle / 2))
    time.sleep(0.5)

    # Single mechanical sweep for azimuth
    for i in range(len(gimbal_positions)):
        mbx.move(gimbal_motor, sweepstep)
        time.sleep(0.3)

        for steering_angle in steering_angles:
            sray.steer_rx(azimuth=steering_angle, elevation=0)
            time.sleep(0.1)

            # Enable all 64 elements for full array measurement
            mr.enable_stingray_channel(sray, subarray.flatten().tolist())
            time.sleep(0.3)

            # Apply analog phase calibration
            for element in sray.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
            sray.latch_rx_settings()
            time.sleep(0.2)

            steer_data = np.transpose(np.array(mr.data_capture(conv)))
            steer_data = np.array(steer_data).T
            steer_data = mr.cal_data(steer_data, cal_ant)
            steer_data = np.array(steer_data).T

            combined_data = np.sum(steer_data, axis=1)

            # Delta weights (your original)
            weights = np.array([1, -1, -1, 1])

            # Magnitudes
            peak_mags_az[steering_angle][i] = mr.get_analog_mag(combined_data)

            combined_data_delta = steer_data @ weights
            peak_mags_az_delta[steering_angle][i] = mr.get_analog_mag(combined_data_delta)

            # Store Σ and Δ IQ explicitly
            all_sum_iq_64[run_idx].append(combined_data)
            all_delta_iq_64[run_idx].append(combined_data_delta)

            # Store magnitudes (Σ and Δ) for mean computation later
            all_powers_64[run_idx].append(peak_mags_az[steering_angle][i])
            all_powers_64_delta[run_idx].append(peak_mags_az_delta[steering_angle][i])

            # Collect IQ data and metadata
            gimbal_angle = angles[i]
            all_iq_data_64[run_idx].append(steer_data)
            all_gimbal_angles_64[run_idx].append(gimbal_angle)
            all_steering_angles_64[run_idx].append(steering_angle)

            # Update live plot for AZ (Σ and Δ) – plot only current run, lightly transparent
            plot_angles = angles[:i + 1]
            plot_power_sum = np.array(peak_mags_az[steering_angle][:i + 1], dtype=float)
            plot_power_delta = np.array(peak_mags_az_delta[steering_angle][:i + 1], dtype=float)

            line_full_array.set_data(plot_angles, plot_power_sum)
            line_delta_array.set_data(plot_angles, plot_power_delta)

            line_full_array.set_alpha(0.35)
            line_delta_array.set_alpha(0.35)

            valid_sum = plot_power_sum[~np.isnan(plot_power_sum)]
            valid_delta = plot_power_delta[~np.isnan(plot_power_delta)]
            valid_data = np.concatenate([valid_sum, valid_delta]) if (valid_sum.size + valid_delta.size) else np.array([])

            if valid_data.size > 0:
                y_min = np.min(valid_data) - 5
                y_max = np.max(valid_data) + 5
                ax_full_array.set_ylim([y_min, y_max])

            ax_full_array.relim()
            ax_full_array.autoscale_view(scalex=False)
            fig_full_array.canvas.draw()
            fig_full_array.canvas.flush_events()

    # =====================================================
    # === ELEVATION LIVE PLOT (Σ and Δ)
    # =====================================================
    plt.ion()
    fig_el_array, ax_el_array = plt.subplots(figsize=(14, 8))
    mng_el = fig_el_array.canvas.manager
    try:
        mng_el.window.showMaximized()
    except:
        pass

    line_full_array_el, = ax_el_array.plot([], [], linestyle='dotted', marker='o', markersize=6,
                                          linewidth=2, color='tab:green', label='El Σ (Sum)')
    line_delta_array_el, = ax_el_array.plot([], [], color="tab:red", linestyle="--",
                                           linewidth=2, marker='d', markersize=5, label="El Δ (Delta)")

    ax_el_array.set_xlabel("Mechanical Elevation Angle (degrees)", fontsize=14)
    ax_el_array.set_ylabel("Combined RF Input Power (dBm)", fontsize=14)
    ax_el_array.set_title(f"RX Elevation Pattern – Σ / Δ (Live) @ {sig_gen_freq_GHz} GHz",
                          fontsize=16, fontweight='bold')
    ax_el_array.set_xlim([-(maxsweepangle / 2), (maxsweepangle / 2)])
    ax_el_array.grid(True, alpha=0.3)
    ax_el_array.legend(fontsize=12, loc='best')

    # --- Reset EL gimbal to start position for this run ---
    gimbal_motor = GIMBAL_V
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle / 2))
    time.sleep(0.5)

    print("Starting Elevation Sweep...")
    gimbal_motor = GIMBAL_V
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle / 2))

    # Define elevation delta weights (your original)
    elevation_weights = np.array([1, 1, -1, -1])

    for i in range(len(gimbal_positions)):
        mbx.move(gimbal_motor, sweepstep)
        time.sleep(0.3)

        for steering_angle in steering_angles:
            sray.steer_rx(azimuth=0, elevation=steering_angle)
            time.sleep(0.1)

            mr.enable_stingray_channel(sray, subarray.flatten().tolist())
            time.sleep(0.3)

            for element in sray.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
            sray.latch_rx_settings()
            time.sleep(0.2)

            steer_data = np.transpose(np.array(mr.data_capture(conv)))
            steer_data = steer_data.T
            steer_data = mr.cal_data(steer_data, cal_ant)
            steer_data = steer_data.T

            combined_data = np.sum(steer_data, axis=1)
            combined_data_delta = steer_data @ elevation_weights

            peak_mags_el[steering_angle][i] = mr.get_analog_mag(combined_data)
            peak_mags_el_delta[steering_angle][i] = mr.get_analog_mag(combined_data_delta)

            # Update live elevation plot
            plot_angles_el = angles[:i + 1]
            plot_power_sum_el = np.array(peak_mags_el[steering_angle][:i + 1], dtype=float)
            plot_power_delta_el = np.array(peak_mags_el_delta[steering_angle][:i + 1], dtype=float)

            line_full_array_el.set_data(plot_angles_el, plot_power_sum_el)
            line_delta_array_el.set_data(plot_angles_el, plot_power_delta_el)

            # FIXED: set alpha on EL lines (not AZ lines)
            line_full_array_el.set_alpha(0.35)
            line_delta_array_el.set_alpha(0.35)

            valid_sum_el = plot_power_sum_el[~np.isnan(plot_power_sum_el)]
            valid_delta_el = plot_power_delta_el[~np.isnan(plot_power_delta_el)]
            valid_data_el = np.concatenate([valid_sum_el, valid_delta_el]) if (valid_sum_el.size + valid_delta_el.size) else np.array([])

            if valid_data_el.size > 0:
                y_min = np.min(valid_data_el) - 5
                y_max = np.max(valid_data_el) + 5
                ax_el_array.set_ylim([y_min, y_max])

            ax_el_array.relim()
            ax_el_array.autoscale_view(scalex=False)
            fig_el_array.canvas.draw()
            fig_el_array.canvas.flush_events()

            # Store EL metadata + IQ + magnitudes
            gimbal_angle = angles[i]
            all_iq_data_64_el[run_idx].append(steer_data)
            all_sum_iq_64_el[run_idx].append(combined_data)
            all_delta_iq_64_el[run_idx].append(combined_data_delta)
            all_gimbal_angles_64_el[run_idx].append(gimbal_angle)
            all_steering_angles_64_el[run_idx].append(steering_angle)

            all_powers_64_el[run_idx].append(peak_mags_el[steering_angle][i])
            all_powers_64_el_delta[run_idx].append(peak_mags_el_delta[steering_angle][i])

    plt.ioff()

# =====================================================
# AFTER ALL RUNS: SAVE PLOTS + DATA ONCE
# =====================================================

# Compute mean traces across runs (true average)
az_sum_mean   = np.nanmean(np.array(all_powers_64, dtype=float), axis=0)
az_delta_mean = np.nanmean(np.array(all_powers_64_delta, dtype=float), axis=0)
el_sum_mean   = np.nanmean(np.array(all_powers_64_el, dtype=float), axis=0)
el_delta_mean = np.nanmean(np.array(all_powers_64_el_delta, dtype=float), axis=0)

def _norm_to_peak_db(x):
    x = np.array(x, dtype=float)
    m = np.nanmax(x)
    return x - m if np.isfinite(m) else x

# Optional normalization for asymmetry visualization
if NORMALIZE_FOR_ASYMMETRY:
    az_sum_plot   = _norm_to_peak_db(az_sum_mean)
    az_delta_plot = _norm_to_peak_db(az_delta_mean)
    el_sum_plot   = _norm_to_peak_db(el_sum_mean)
    el_delta_plot = _norm_to_peak_db(el_delta_mean)
    y_label = "Relative Power (dB)"
    title_suffix = " (Normalized to Peak)"
else:
    az_sum_plot   = az_sum_mean
    az_delta_plot = az_delta_mean
    el_sum_plot   = el_sum_mean
    el_delta_plot = el_delta_mean
    y_label = "Combined RF Input Power (dBm)"
    title_suffix = ""

# ------------------------------
# Save combined 4-trace overlay
# ------------------------------
if SAVE_COMBINED_4TRACE_PNG:
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(angles, az_sum_plot,   color="tab:blue",   linewidth=2, marker="o", markersize=4, label="Az Σ (Sum)")
    ax.plot(angles, az_delta_plot, color="tab:orange", linewidth=2, linestyle="--", marker="s", markersize=4, label="Az Δ (Delta)")
    ax.plot(angles, el_sum_plot,   color="tab:green",  linewidth=2, marker="^", markersize=4, label="El Σ (Sum)")
    ax.plot(angles, el_delta_plot, color="tab:red",    linewidth=2, linestyle="--", marker="d", markersize=4, label="El Δ (Delta)")

    ax.axhline(0, color="gray", linestyle=":", linewidth=1)

    ax.set_title(
        f"Manta Ray RX Monopulse Overlay: Az vs El (Σ / Δ){title_suffix}\n"
        f"{sig_gen_freq_GHz} GHz, Steering = 0°",
        fontsize=16, fontweight="bold"
    )
    ax.set_xlabel("Mechanical Angle (degrees)", fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    ax.set_xlim([-(maxsweepangle / 2), (maxsweepangle / 2)])
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12, loc="best", frameon=True)

    # Auto y-limits
    all_traces = np.concatenate([
        az_sum_plot[~np.isnan(az_sum_plot)],
        az_delta_plot[~np.isnan(az_delta_plot)],
        el_sum_plot[~np.isnan(el_sum_plot)],
        el_delta_plot[~np.isnan(el_delta_plot)],
    ])
    if all_traces.size > 0:
        ax.set_ylim([np.min(all_traces) - 5, np.max(all_traces) + 5])

    combined_overlay_png_path = os.path.join(
        base_out_dir,
        f"rx_monopulse_sum_delta_AZ_EL_overlay_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )

    plt.tight_layout()
    plt.savefig(combined_overlay_png_path, dpi=200)
    plt.close()

    print(f"Saved AZ+EL Σ/Δ combined overlay plot to: {combined_overlay_png_path}")

# ------------------------------
# Save separate AZ overlay
# ------------------------------
if SAVE_SEPARATE_AZ_EL_PNGS:
    plt.figure(figsize=(12, 7))
    plt.plot(angles, az_sum_mean, color="tab:blue", linewidth=2, marker="o", label="Az Σ (Sum) Mean")
    plt.plot(angles, az_delta_mean, color="tab:orange", linewidth=2, linestyle="--", marker="s", label="Az Δ (Delta) Mean")
    plt.axhline(0, color="gray", linestyle=":", linewidth=1)

    plt.title(
        f"Manta Ray RX Azimuth Monopulse Pattern (Σ / Δ)\n"
        f"{sig_gen_freq_GHz} GHz, Steering = 0°",
        fontsize=16, fontweight="bold"
    )
    plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=14)
    plt.ylabel("Combined RF Input Power (dBm)", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.xlim([-(maxsweepangle / 2), (maxsweepangle / 2)])

    az_overlay_png_path = os.path.join(
        base_out_dir,
        f"rx_monopulse_sum_delta_azimuth_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )
    plt.tight_layout()
    plt.savefig(az_overlay_png_path, dpi=200)
    plt.close()
    print(f"Saved AZ Σ/Δ overlay plot to: {az_overlay_png_path}")

    # ------------------------------
    # Save separate EL overlay
    # ------------------------------
    plt.figure(figsize=(12, 7))
    plt.plot(angles, el_sum_mean, color="tab:green", linewidth=2, marker="^", label="El Σ (Sum) Mean")
    plt.plot(angles, el_delta_mean, color="tab:red", linestyle="--", linewidth=2, marker="d", label="El Δ (Delta) Mean")
    plt.axhline(0, color="gray", linestyle=":", linewidth=1)

    plt.title(
        f"Manta Ray RX Elevation Monopulse Pattern (Σ / Δ)\n"
        f"{sig_gen_freq_GHz} GHz, Steering = 0°",
        fontsize=16, fontweight="bold"
    )
    plt.xlabel("Mechanical Elevation Angle (degrees)", fontsize=14)
    plt.ylabel("Combined RF Input Power (dBm)", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.xlim([-(maxsweepangle / 2), (maxsweepangle / 2)])

    el_overlay_png_path = os.path.join(
        base_out_dir,
        f"rx_monopulse_sum_delta_elevation_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )
    plt.tight_layout()
    plt.savefig(el_overlay_png_path, dpi=200)
    plt.close()
    print(f"Saved EL Σ/Δ overlay plot to: {el_overlay_png_path}")

# =====================================================
# Save all IQ data to combined .mat files (AZ + EL)
# =====================================================
iq_save_dir = os.path.join(base_out_dir, "raw_iq_data")
os.makedirs(iq_save_dir, exist_ok=True)

combined_iq_mat_path_az = os.path.join(
    iq_save_dir,
    f"raw_iq_full_64element_combined_azimuth_sweep_{sig_gen_freq_GHz}GHz_{timestamp}.mat"
)

combined_iq_dict_az = {
    "scan_axis": "azimuth",
    "subarray_iq": np.array(all_iq_data_64, dtype=object),
    "sum_iq": np.array(all_sum_iq_64, dtype=object),
    "delta_iq": np.array(all_delta_iq_64, dtype=object),

    "gimbal_angles_deg": np.array(all_gimbal_angles_64, dtype=object),
    "steering_angles_deg": np.array(all_steering_angles_64, dtype=object),

    "sum_power_dBm": np.array(all_powers_64, dtype=object),
    "delta_power_dBm": np.array(all_powers_64_delta, dtype=object),

    "mechanical_angles_deg": np.array(angles),
    "angles_deg": np.array(angles),
    "frequency_GHz": float(sig_gen_freq_GHz),
    "sample_rate_Hz": float(fs_RxIQ),
    "weights_delta": np.array([1, -1, -1, 1]),
    "num_repeats": int(NUM_REPEATS),

    "description": (
        "Manta Ray RX azimuth sweep. "
        "Contains calibrated subarray IQ, sum (Σ) IQ, and delta (Δ) IQ + magnitudes."
    ),
}

savemat(combined_iq_mat_path_az, combined_iq_dict_az, do_compression=True)
print(f"\nSaved AZ IQ data to: {combined_iq_mat_path_az}")

combined_iq_mat_path_el = os.path.join(
    iq_save_dir,
    f"raw_iq_full_64element_combined_elevation_sweep_{sig_gen_freq_GHz}GHz_{timestamp}.mat"
)

combined_iq_dict_el = {
    "scan_axis": "elevation",
    "subarray_iq": np.array(all_iq_data_64_el, dtype=object),
    "sum_iq": np.array(all_sum_iq_64_el, dtype=object),
    "delta_iq": np.array(all_delta_iq_64_el, dtype=object),

    "gimbal_angles_deg": np.array(all_gimbal_angles_64_el, dtype=object),
    "steering_angles_deg": np.array(all_steering_angles_64_el, dtype=object),

    "sum_power_dBm": np.array(all_powers_64_el, dtype=object),
    "delta_power_dBm": np.array(all_powers_64_el_delta, dtype=object),

    "mechanical_angles_deg": np.array(angles),
    "angles_deg": np.array(angles),
    "frequency_GHz": float(sig_gen_freq_GHz),
    "sample_rate_Hz": float(fs_RxIQ),
    "weights_delta": np.array(elevation_weights),
    "num_repeats": int(NUM_REPEATS),

    "description": "Manta Ray RX elevation sweep. Contains Σ/Δ IQ + magnitudes.",
}

savemat(combined_iq_mat_path_el, combined_iq_dict_el, do_compression=True)
print(f"Saved EL IQ data to: {combined_iq_mat_path_el}")

mbx.gotoZERO()
print("Done. Gimbal returned to ZERO.")

# # Save data to MATLAB file with both azimuth and elevation patterns
# matlab_data = {
#     'mechanical_angles': angles,
#     'steering_angles': steering_angles,
#     'cal_antenna': cal_ant,
#     # Azimuth patterns (convert to dBm)
#     # 'measured_patterns_az_neg45': peak_mags_az[-45],
#     # 'measured_patterns_az_neg30': peak_mags_az[-30],
#     # 'measured_patterns_az_neg15': peak_mags_az[-15],
#     'measured_patterns_az_0': peak_mags_az[0],
#     # 'measured_patterns_az_pos15': peak_mags_az[15],
#     # 'measured_patterns_az_pos30': peak_mags_az[30],
#     # 'measured_patterns_az_pos45': peak_mags_az[45],
#     # Elevation patterns (convert to dBm)
#     # 'measured_patterns_el_neg60': peak_mags_el[-60] - 10.2,
#     # 'measured_patterns_el_neg45': peak_mags_el[-45] - 10.2,
#     # 'measured_patterns_el_neg30': peak_mags_el[-30] - 10.2,
#     # 'measured_patterns_el_neg15': peak_mags_el[-15] - 10.2,
#     # 'measured_patterns_el_0': peak_mags_el[0] - 10.2,
#     # 'measured_patterns_el_pos15': peak_mags_el[15] - 10.2,
#     # 'measured_patterns_el_pos30': peak_mags_el[30] - 10.2,
#     # 'measured_patterns_el_pos45': peak_mags_el[45] - 10.2,
#     # 'measured_patterns_el_pos60': peak_mags_el[60] - 10.2
# }

# # Save combined azimuth and elevation data
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# savemat(f'/home/snuc/Desktop/rx_beamforming_patterns_azel_{timestamp}.mat', matlab_data)

# # Create plots for both azimuth and elevation patterns
# plt.ioff()  # Turn off interactive mode for batch saving

# # Plot and save azimuth patterns
# for steering_angle in steering_angles:
#     plt.figure(figsize=(10, 6))
#     plt.plot(angles, peak_mags_az[steering_angle] - 10.2,  # Convert to dBm
#              linestyle='dotted', label='Measured Data', 
#              color='blue', markersize=9)
#     plt.title(f'Azimuth Pattern (Steering Angle: {steering_angle}°)')
#     plt.xlabel('Mechanical Azimuth Angle (degrees)')
#     plt.ylabel('Combined RF Input Power (dBm)')
#     plt.ylim(-60, 0)
#     plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
#     plt.grid(True)
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(f'/home/snuc/Desktop/azimuth_pattern_{steering_angle}deg_{timestamp}.png')
#     plt.close()