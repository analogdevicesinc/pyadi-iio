# Manta Ray 64 Element Electronic Steering Array Calibration and Sweep
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import time
import importlib
import genalyzer as gn
import adi
from adi.sshfs import sshfs
import os
os.environ['QT_QPA_PLATFORM'] = 'wayland'
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime
# import adar_functions
import re
import json
import os
import pandas as pd
from scipy.special import factorial
from scipy.io import savemat
import MantaRay as mr
import pyvisa
import math
rm = pyvisa.ResourceManager()
# Import from Drivers folder (subfolder relative to this file)
from Drivers import N9000A_Driver as N9000A
from Drivers import E8267D_Driver as E8267D
from Drivers import N6705B_Driver as N6705B
from Drivers import E36233A_Driver as E36233A
# Import from Millibox folder (subfolder relative to this file)
from Millibox import mbx_functions as mbx


BAUDRATE                    = 57600                    
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

##############################################
## Step 1: Initial Array ##
###############################################
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

talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip


## Set TR Source, Mode, and Bias DAC Mode ##
## toggle with respect to T/R state.
for device in dev.devices.values():
    device.tr_source = "spi"
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


dev.latch_tx_settings()
dev.latch_rx_settings()
print("Initialized BFC Tile")

mr.disable_pa_bias_channel(dev)
PA_Supplies.output_on(1)




array_shapes =[[19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46], 
              [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46,10, 18, 26, 34, 42, 50, 51, 52, 53, 54, 55, 47, 39, 31, 23, 15, 14, 13, 12, 11],
              [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64],
              [1,2,3,4,5,6,7,8,9,17,25,33,41,49,57,58,59,60,61,62,63,64,56,48,40,32,24,16],
              [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],
              [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],
              [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],
              [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],
              [37]
              ]

#\# Define the 4 Tx subarrays (each 4x4 = 16 elements) \#\#
# array_shapes[4..7] already correspond to subarray 4..1 in this script
subarrays = {
    'subarray 1': array_shapes[7],
    'subarray 2': array_shapes[6],
    'subarray 3': array_shapes[5],
    'subarray 4': array_shapes[4],
}

# If you only want a subset, edit this list (default = all four)
subarray_run_order = ['subarray 1', 'subarray 2', 'subarray 3', 'subarray 4']

##############################################
## Step 2: Initialize Gimbal and Beamsteer ##
###############################################

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

sig_gen_freq_GHz=10
beamsteering = False
steering_angle = 0 # degrees
maxsweepangle = 120  # degrees
sweepstep = 1
gimbal_motor = GIMBAL_H
gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)  # Define gimbal positions from -90 to 90 degrees

SpecAn_Values = []


# # ---- Capture current calibrated phases/gains for all 64 elements once ----
# These are used as a reference so that when dev.steer_tx() writes new phases,
# we can apply an offset correction during the sweep.
phase_dict = {i: 0.0 for i in range(1, 65)}
mag_dict   = {i: 0.0 for i in range(1, 65)}
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    phase_dict[value] = element.tx_phase
    mag_dict[value]   = element.tx_gain

## Set TR Source to external and bias_dac_mode to toggle ##
for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"


mechanical_sweep, elec_steer_angle, azim_results, elev_results, = mr.calc_array_pattern(theta_sweep=(-90, 90), elec_steer_angle=steering_angle,f_op_GHz=9.994, M=8, N=8)

# Define the corresponding angles (assuming gimbal_positions is 0 to 80, map to -40 to 40)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))

# plt.figure(figsize=(10, 6))

# Calculate and plot
mechanical_sweep, elec_steer_angle, azim_results, elev_results, = mr.calc_array_pattern(elec_steer_angle=steering_angle,f_op_GHz=sig_gen_freq_GHz)


# Define steering angles to test
# steering_angles = [-45, -30, -15, 0, 15, 30, 45]
steering_angles = [0]
# Initialize arrays for both azimuth and elevation
peak_mags_az = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
peak_mags_el = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
azim_results_all = {}
elev_results_all = {}

# \# === Azimuth Sweep (per-subarray) ===

def run_azimuth_sweep_combined(subarrays, subarray_run_order, f_GHz, angles, gimbal_positions, sweepstep, maxsweepangle, steering_angles, dev):
    """Run a mechanical azimuth sweep for ALL subarrays simultaneously with live combined plot.
    
    Measures each subarray at each gimbal angle and plots all 4 on the same live plot.
    Returns peak_mags_az dict: {subarray_name: {steering_angle: np.array(len(gimbal_positions))}}.
    """
    
    print(f"Starting Combined Azimuth Sweep for all subarrays @ {f_GHz} GHz...")
    gimbal_motor = GIMBAL_H
    
    # Initialize data storage: {subarray_name: {steering_angle: [powers]}}
    all_peak_mags_az = {sa_name: {angle: np.full(len(gimbal_positions), np.nan) for angle in steering_angles} 
                        for sa_name in subarray_run_order}
    
    # Interactive combined plot
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Maximize the plot window
    mng = fig.canvas.manager
    mng.window.showMaximized()
    
    ax.set_title(f"Azimuth Pattern (Combined Real-time) - All Subarrays @ {f_GHz} GHz", fontsize=14, fontweight='bold')
    ax.set_xlabel("Mechanical Azimuth Angle (degrees)", fontsize=12)
    ax.set_ylabel("Combined RF Input Power (dBm)", fontsize=12)
    ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    ax.grid(True, alpha=0.3)
    
    # Colors and markers for each subarray
    colors = ['blue', 'red', 'green', 'purple']
    markers = ['o', 's', '^', 'D']
    
    # Restart from -max/2
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle/2))
    
    for i in range(len(gimbal_positions)):
        print(f"Gimbal position {i}/{len(gimbal_positions)-1}: {angles[i]:.1f}°")
        
        # At this gimbal angle, measure all 4 subarrays
        for subarray_idx, subarray_name in enumerate(subarray_run_order):
            active_array = list(map(int, list(subarrays[subarray_name])))
            active_set = set(active_array)
            
            # Enable PA bias only for this subarray
            mr.enable_pa_bias_channel(dev, active_array)
            time.sleep(0.5)
            
            for steering_angle in steering_angles:
                dev.steer_tx(azimuth=steering_angle, elevation=0)
                dev.latch_tx_settings()
                
                # Apply analog phase calibration ONLY on active channels
                for element in dev.elements.values():
                    str_channel = str(element)
                    value = int(mr.strip_to_last_two_digits(str_channel))
                    if value in active_set:
                        element.tx_phase = (phase_dict[value] - element.tx_phase) % 360
                dev.latch_tx_settings()
                
                time.sleep(0.5)
                all_peak_mags_az[subarray_name][steering_angle][i] = SpecAn.get_marker_power(marker=1)
            
            # Disable this subarray before moving to the next
            mr.disable_pa_bias_channel(dev, active_array)
            time.sleep(0.3)
        
        # Update combined real-time plot with all subarrays
        ax.clear()
        x = angles[: i + 1]
        
        for subarray_idx, subarray_name in enumerate(subarray_run_order):
            for steering_angle in steering_angles:
                y = all_peak_mags_az[subarray_name][steering_angle][: i + 1]
                ax.plot(x, y, linestyle="dotted", marker=markers[subarray_idx], markersize=5, 
                       linewidth=2, label=f"{subarray_name} (SA={steering_angle}°)", color=colors[subarray_idx])
        
        ax.set_title(f"Azimuth Pattern (Combined Real-time) - All Subarrays @ {f_GHz} GHz", fontsize=14, fontweight='bold')
        ax.set_xlabel("Mechanical Azimuth Angle (degrees)", fontsize=12)
        ax.set_ylabel("Combined RF Input Power (dBm)", fontsize=12)
        ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        
        # Auto-scale y-axis
        all_data = np.concatenate([np.asarray(all_peak_mags_az[sa][steer_ang][: i + 1]) 
                                   for sa in subarray_run_order for steer_ang in steering_angles if np.any(~np.isnan(all_peak_mags_az[sa][steer_ang][: i + 1]))])
        if len(all_data) > 0:
            y_min = np.nanmin(all_data) - 10
            y_max = np.nanmax(all_data) + 10
            ax.set_ylim(y_min, y_max)
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=10)
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)
        
        # Move gimbal for next position
        mbx.move(gimbal_motor, sweepstep)
    
    # Finish sweep
    mbx.gotoZERO()
    
    # Set phases back to calibrated phases (all elements)
    for element in dev.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.tx_phase = phase_dict[value]
    dev.latch_tx_settings()
    
    plt.ioff()
    return all_peak_mags_az


def run_azimuth_sweep(active_array, subarray_name, f_GHz, angles, gimbal_positions, sweepstep, maxsweepangle, steering_angles):
    """Run a mechanical azimuth sweep for a given subarray.

    Only enables PA bias on the specified active_array elements.
    Returns peak_mags_az dict: {steering_angle: np.array(len(gimbal_positions))}.
    """
    active_array = list(map(int, list(active_array)))
    active_set = set(active_array)

    print(f"Starting Azimuth Sweep for {subarray_name} @ {f_GHz} GHz...")
    gimbal_motor = GIMBAL_H

    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle/2))

    # Enable PA bias only for this subarray
    mr.enable_pa_bias_channel(dev, active_array)
    time.sleep(3)

    peak_mags_az = {angle: np.full(len(gimbal_positions), np.nan) for angle in steering_angles}

    # Interactive plot (one figure per subarray)
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"Azimuth Pattern (real-time) - {subarray_name} @ {f_GHz} GHz")
    ax.set_xlabel("Mechanical Azimuth Angle (degrees)")
    ax.set_ylabel("Combined RF Input Power (dBm)")
    ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    ax.grid(True)

    # Restart from -max/2 so the plot aligns to angles[]
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle/2))

    for i in range(len(gimbal_positions)):
        for steering_angle in steering_angles:
            dev.steer_tx(azimuth=steering_angle, elevation=0)
            dev.latch_tx_settings()

            # Apply analog phase calibration ONLY on active channels
            for element in dev.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                if value in active_set:
                    element.tx_phase = (phase_dict[value] - element.tx_phase) % 360
            dev.latch_tx_settings()

            time.sleep(0.5)
            peak_mags_az[steering_angle][i] = SpecAn.get_marker_power(marker=1)

        # update real-time plot
        ax.clear()
        x = angles[: i + 1]
        for sa in steering_angles:
            y = peak_mags_az[sa][: i + 1]
            ax.plot(x, y, linestyle="dotted", marker="o", markersize=4, label=f"Measured SA={sa}°")
        ax.set_title(f"Azimuth Pattern (real-time) - {subarray_name} @ {f_GHz} GHz")
        ax.set_xlabel("Mechanical Azimuth Angle (degrees)")
        ax.set_ylabel("Combined RF Input Power (dBm)")
        ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])

        all_data = np.concatenate([np.asarray(peak_mags_az[sa][: i + 1]) for sa in steering_angles])
        if len(all_data) > 0:
            y_min = np.nanmin(all_data) - 10
            y_max = np.nanmax(all_data) + 10
            ax.set_ylim(y_min, y_max)
        ax.grid(True)
        ax.legend(loc="best")
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)

        mbx.move(gimbal_motor, sweepstep)

    # finish sweep
    mbx.gotoZERO()
    mr.disable_pa_bias_channel(dev, active_array)

    # Set phases back to calibrated phases (all elements)
    for element in dev.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.tx_phase = phase_dict[value]
    dev.latch_tx_settings()

    plt.ioff()
    return peak_mags_az


# ---- Output folder setup ----
# All per-subarray outputs will go under this folder
base_out_dir = "/home/snuc/Desktop/subarray plots"
os.makedirs(base_out_dir, exist_ok=True)

# ---- Run the combined azimuth sweep for all subarrays with live plot ----
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

all_subarray_results = run_azimuth_sweep_combined(
    subarrays=subarrays,
    subarray_run_order=subarray_run_order,
    f_GHz=sig_gen_freq_GHz,
    angles=angles,
    gimbal_positions=gimbal_positions,
    sweepstep=sweepstep,
    maxsweepangle=maxsweepangle,
    steering_angles=steering_angles,
    dev=dev
)

# Save raw data and individual plots for each subarray
for subarray_name in subarray_run_order:
    # Create subfolder for this subarray
    sub_dir = os.path.join(base_out_dir, subarray_name.replace(' ', '_'))
    os.makedirs(sub_dir, exist_ok=True)

    peak_mags_az = all_subarray_results[subarray_name]

    # Save raw data (power vs angle) as MATLAB .mat inside the subarray folder
    # One MAT-file per steering angle
    for steering_angle in steering_angles:
        mat_path = os.path.join(
            sub_dir,
            f"power_vs_angle_{subarray_name.replace(' ', '_')}_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.mat"
        )
    
        mdict = {
            "angles_deg": angles.reshape(-1, 1),                 # Nx1
            "power_dBm": peak_mags_az[steering_angle].reshape(-1, 1),  # Nx1
            "steering_angle_deg": steering_angle,
            "frequency_GHz": sig_gen_freq_GHz,
            "subarray": subarray_name,
        }
    
        savemat(mat_path, mdict, do_compression=True)
        print(f"Saved {subarray_name} data to {mat_path}")

    # Save an individual PNG per subarray (per steering angle)
    for steering_angle in steering_angles:
        plt.figure(figsize=(10, 6))
        plt.plot(
            angles,
            peak_mags_az[steering_angle],
            linestyle="dotted",
            marker="o",
            markersize=4,
            label=f"{subarray_name} measured",
        )
        plt.title(f"Azimuth Pattern - {subarray_name} @ {sig_gen_freq_GHz} GHz (SA={steering_angle}°)")
        plt.xlabel("Mechanical Azimuth Angle (degrees)")
        plt.ylabel("Combined RF Input Power (dBm)")
        plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(sub_dir, f"Tx_azimuth_{subarray_name.replace(' ', '_')}_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.png"))
        plt.close()

# Optional: also create a single 2x2 overview figure for SA=0 (if present)
try:
    if 0 in steering_angles:
        fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
        order = subarray_run_order
        for ax, name in zip(axs.ravel(), order):
            y = all_subarray_results[name][0]
            ax.plot(angles, y, linestyle="dotted", marker="o", markersize=3)
            ax.set_title(f"{name} @ {sig_gen_freq_GHz} GHz")
            ax.grid(True)
        fig.suptitle(f"Azimuth Pattern Overview (SA=0°) @ {sig_gen_freq_GHz} GHz")
        for ax in axs[-1, :]:
            ax.set_xlabel("Mechanical Azimuth Angle (degrees)")
        for ax in axs[:, 0]:
            ax.set_ylabel("Combined RF Input Power (dBm)")
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(os.path.join(base_out_dir, f"Tx_azimuth_overview_SA0_{sig_gen_freq_GHz}GHz_{timestamp}.png"))
        plt.close(fig)
except Exception as e:
    print(f"Overview plot generation skipped due to: {e}")

# Create combined overlay plot with all subarrays on one graph
try:
    colors = ['blue', 'red', 'green', 'purple']
    markers = ['o', 's', '^', 'D']
    
    for steering_angle in steering_angles:
        plt.figure(figsize=(14, 8))
        
        order = subarray_run_order
        for idx, name in enumerate(order):
            y = all_subarray_results[name][steering_angle]
            plt.plot(
                angles,
                y,
                linestyle="dotted",
                marker=markers[idx],
                markersize=5,
                linewidth=2,
                label=f"{name}",
                color=colors[idx]
            )
        
        plt.title(f"TX Azimuth Pattern - All Subarrays @ {sig_gen_freq_GHz} GHz (SA={steering_angle}°)", fontsize=16, fontweight='bold')
        plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=14)
        plt.ylabel("Combined RF Input Power (dBm)", fontsize=14)
        plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12, loc='best')
        plt.tight_layout()
        
        combined_plot_path = os.path.join(base_out_dir, f"Tx_azimuth_combined_all_subarrays_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.png")
        plt.savefig(combined_plot_path, dpi=150)
        plt.close()
        print(f"Saved combined plot to {combined_plot_path}")
        
except Exception as e:
    print(f"Combined overlay plot generation failed: {e}")

#####################################################################
## INCREMENTAL ELEMENT TEST FOR SUBARRAY 2 (DAMAGE DIAGNOSIS) ##
#####################################################################

print("\n" + "="*70)
print("STARTING INCREMENTAL ELEMENT TEST FOR SUBARRAY 2")
print("="*70)

# Define test parameters
test_maxsweepangle = 60  # -60 to +60 degrees
test_sweepstep = 1
test_gimbal_positions = np.arange(0, (test_maxsweepangle+1), test_sweepstep)
test_angles = np.linspace(-(test_maxsweepangle/2), (test_maxsweepangle/2), len(test_gimbal_positions))

# Get subarray 2 elements
subarray_2_elements = list(map(int, list(subarrays['subarray 2'])))
print(f"Subarray 2 elements: {subarray_2_elements}")

# Storage for all 16 configurations
incremental_results = {}  # {num_elements: np.array(power_values)}

# Create output directory for this test
test_out_dir = os.path.join(base_out_dir, "subarray_2_incremental_element_test")
os.makedirs(test_out_dir, exist_ok=True)

# Interactive plot setup
plt.ion()
fig_incr, ax_incr = plt.subplots(figsize=(14, 10))

# Loop through 1 to 16 elements
for num_elements in range(1, 17):
    print(f"\n--- Testing with {num_elements} element(s) ---")
    
    # Select first N elements from subarray 2
    active_elements = subarray_2_elements[:num_elements]
    print(f"Active elements: {active_elements}")
    
    # Disable all elements first, then enable only the active ones
    mr.disable_pa_bias_channel(dev, subarray_2_elements)
    time.sleep(0.5)
    mr.enable_pa_bias_channel(dev, active_elements)
    time.sleep(1)
    
    # Initialize power array for this configuration
    power_data = np.full(len(test_gimbal_positions), np.nan)
    
    # Reset gimbal to start position
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(test_maxsweepangle/2))
    time.sleep(0.5)
    
    # Sweep gimbal and collect power data
    for i in range(len(test_gimbal_positions)):
        try:
            # Steer TX (all elements, but only active ones have PA bias)
            dev.steer_tx(azimuth=0, elevation=0)
            dev.latch_tx_settings()
            
            # Apply phase calibration for active elements only
            for element in dev.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                if value in active_elements:
                    element.tx_phase = (phase_dict[value] - element.tx_phase) % 360
            dev.latch_tx_settings()
            
            time.sleep(0.3)
            power_data[i] = SpecAn.get_marker_power(marker=1)
            
        except Exception as e:
            print(f"Error at gimbal position {i}: {e}")
            power_data[i] = np.nan
        
        # Move gimbal
        mbx.move(gimbal_motor, test_sweepstep)
    
    # Store results
    incremental_results[num_elements] = power_data
    print(f"Power range: {np.nanmin(power_data):.2f} to {np.nanmax(power_data):.2f} dBm")
    
    # Update real-time plot
    ax_incr.clear()
    for ne in range(1, num_elements + 1):
        if ne in incremental_results:
            ax_incr.plot(test_angles, incremental_results[ne], 
                        linestyle='dotted', marker='o', markersize=3,
                        label=f"{ne} element(s)")
    
    ax_incr.set_title(f"Subarray 2 Incremental Element Test (Gimbal: -60 to +60°) @ {sig_gen_freq_GHz} GHz")
    ax_incr.set_xlabel("Mechanical Azimuth Angle (degrees)")
    ax_incr.set_ylabel("RF Power (dBm)")
    ax_incr.set_xlim([-(test_maxsweepangle/2), (test_maxsweepangle/2)])
    ax_incr.grid(True)
    ax_incr.legend(loc='best', fontsize=8)
    fig_incr.canvas.draw()
    fig_incr.canvas.flush_events()
    plt.pause(0.1)

# Return gimbal to home
mbx.gotoZERO()
mr.disable_pa_bias_channel(dev, subarray_2_elements)

plt.ioff()

# Save final plot with all 16 configurations
plt.figure(figsize=(16, 10))
colors = plt.cm.viridis(np.linspace(0, 1, 16))
for num_elements in range(1, 17):
    plt.plot(test_angles, incremental_results[num_elements], 
            linestyle='dotted', marker='o', markersize=4, linewidth=2,
            label=f"{num_elements} element(s)", color=colors[num_elements-1])

plt.title(f"Subarray 2 Incremental Element Test - All Configurations @ {sig_gen_freq_GHz} GHz", fontsize=16, fontweight='bold')
plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=12)
plt.ylabel("RF Power (dBm)", fontsize=12)
plt.xlim([-(test_maxsweepangle/2), (test_maxsweepangle/2)])
plt.grid(True, alpha=0.3)
plt.legend(loc='best', ncol=2, fontsize=10)
plt.tight_layout()
plot_path = os.path.join(test_out_dir, f"subarray_2_incremental_all_configs_{sig_gen_freq_GHz}GHz_{timestamp}.png")
plt.savefig(plot_path, dpi=150)
print(f"\nSaved combined plot to {plot_path}")
plt.close()

# Save individual plots for each configuration
for num_elements in range(1, 17):
    plt.figure(figsize=(12, 8))
    plt.plot(test_angles, incremental_results[num_elements], 
            linestyle='dotted', marker='o', markersize=5, linewidth=2, color='blue')
    plt.title(f"Subarray 2 with {num_elements} Element(s) @ {sig_gen_freq_GHz} GHz", fontsize=14, fontweight='bold')
    plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=12)
    plt.ylabel("RF Power (dBm)", fontsize=12)
    plt.xlim([-(test_maxsweepangle/2), (test_maxsweepangle/2)])
    plt.grid(True)
    plt.tight_layout()
    individual_plot_path = os.path.join(test_out_dir, f"subarray_2_config_{num_elements}elem_{sig_gen_freq_GHz}GHz_{timestamp}.png")
    plt.savefig(individual_plot_path, dpi=150)
    plt.close()

# Save all data to MAT file
mat_data = {
    "angles_deg": test_angles.reshape(-1, 1),
    "frequency_GHz": sig_gen_freq_GHz,
    "subarray": "subarray 2",
    "test_type": "incremental_element_diagnosis",
}

# Add power data for each configuration
for num_elements in range(1, 17):
    mat_data[f"power_{num_elements}_elements"] = incremental_results[num_elements].reshape(-1, 1)

mat_file_path = os.path.join(test_out_dir, f"subarray_2_incremental_element_data_{sig_gen_freq_GHz}GHz_{timestamp}.mat")
savemat(mat_file_path, mat_data, do_compression=True)
print(f"Saved MAT file to {mat_file_path}")

print("\n" + "="*70)
print("INCREMENTAL ELEMENT TEST COMPLETE")
print("="*70)

# Stop here (elevation sweep below is unchanged but not used in this per-subarray azimuth workflow)
exit()

# # === Elevation Sweep ===
print("Starting Elevation Sweep...")
gimbal_motor = GIMBAL_V
mbx.gotoZERO()
mbx.move(gimbal_motor,-(maxsweepangle/2))
mr.enable_pa_bias_channel(dev, active_array)
time.sleep(3)

# # Single mechanical sweep for elevation
for i in range(len(gimbal_positions)):
    # mr.enable_pa_bias_channel(dev, active_array)
    # time.sleep(3)
    
    for steering_angle in steering_angles:
        dev.steer_tx(azimuth=0, elevation=steering_angle)
        dev.latch_tx_settings()
        # Apply analog phase calibration
        for element in dev.elements.values():
            str_channel = str(element)
            value = int(mr.strip_to_last_two_digits(str_channel))
            element.tx_phase = (phase_dict[value] - element.tx_phase) % 360
        
        dev.latch_tx_settings()
        time.sleep(0.5)
        peak_mags_el[steering_angle][i] = SpecAn.get_marker_power(marker=1)

    mbx.move(gimbal_motor, sweepstep)
    # mr.disable_pa_bias_channel(dev, active_array)
mbx.gotoZERO()
mr.disable_pa_bias_channel(dev, active_array)
#Set Phases back to calibrated phases
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.tx_phase = (phase_dict[value])

mbx.gotoZERO()

# Save data to MATLAB file with both azimuth and elevation patterns





# # Create plots for both azimuth and elevation patterns
# plt.ioff()  # Turn off interactive mode for batch saving

# Plot and save azimuth patterns
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
for steering_angle in steering_angles:
    plt.figure(figsize=(10, 6))
    plt.plot(angles, peak_mags_az[steering_angle],  # Convert to dBm
             linestyle='dotted', label='Measured Data', 
             color='blue', markersize=9)
    plt.title(f'Azimuth Pattern (Steering Angle: {steering_angle}°)')
    plt.xlabel('Mechanical Azimuth Angle (degrees)')
    plt.ylabel('Combined RF Input Power (dBm)')
    plt.ylim(-80, 0)
    plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'/home/snuc/Desktop/Tx_azimuth_pattern_{steering_angle}deg_{timestamp}.png')
    plt.close()


a=1
# # Plot and save elevation patterns
for steering_angle in steering_angles:
    plt.figure(figsize=(10, 6))
    plt.plot(angles, peak_mags_el[steering_angle],  # Convert to dBm
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




# ==== Minimal MATLAB .m export (simple variables only) ====

def _mat_row(vec):
    import numpy as _np
    return "[" + " ".join(f"{float(x):.10g}" for x in _np.asarray(vec).ravel()) + "]"

def _matrix_to_matlab(M):
    """
    Convert a 2D numpy array to MATLAB matrix literal with rows separated by ';'
    """
    import numpy as _np
    if M.size == 0:
        return "[]"
    rows = []
    for i in range(M.shape[0]):
        row = " ".join(f"{float(x):.10g}" for x in M[i, :])
        rows.append("  " + row)
    return "[\n" + ";\n".join(rows) + "\n]"

# Prepare azimuth arrays
import numpy as _np
az_keys = sorted(peak_mags_az.keys(), key=float) if peak_mags_az else []
if az_keys:
    az_matrix = _np.column_stack([_np.asarray(peak_mags_az[k]).ravel() for k in az_keys])
else:
    az_matrix = _np.zeros((len(angles), 0))

# Prepare elevation arrays (may be empty if elevation sweep disabled)
el_keys = sorted(peak_mags_el.keys(), key=float) if peak_mags_el else []
if el_keys:
    el_matrix = _np.column_stack([_np.asarray(peak_mags_el[k]).ravel() for k in el_keys])
else:
    el_matrix = _np.zeros((len(angles), 0))

# Ensure az/el vectors match the angles length (basic guard)
if az_matrix.shape[0] and az_matrix.shape[0] != len(angles):
    raise ValueError("Azimuth data length does not match angles length.")
if el_matrix.shape[0] and el_matrix.shape[0] != len(angles):
    raise ValueError("Elevation data length does not match angles length.")

m_path = "/home/snuc/Desktop/beam_sweeps.m"
with open(m_path, "w") as f:
    f.write("%% Auto-generated sweep data from Python\n")
    f.write("%% Variables: angles, az_steering_angles, az_power, el_steering_angles, el_power\n\n")

    # Angles (column vector)
    f.write(f"angles = {_mat_row(angles)}';  % Nx1 mechanical angles (deg)\n\n")

    # Azimuth
    if az_keys:
        f.write(f"az_steering_angles = {_mat_row(az_keys)};  % 1xM steering angles (deg)\n")
        f.write(f"az_power = {_matrix_to_matlab(az_matrix)};  % NxM, dBm\n\n")
    else:
        f.write("az_steering_angles = [];\naz_power = [];\n\n")

    # Elevation
    if el_keys:
        f.write(f"el_steering_angles = {_mat_row(el_keys)};  % 1xK steering angles (deg)\n")
        f.write(f"el_power = {_matrix_to_matlab(el_matrix)};  % NxK, dBm\n\n")
    else:
        f.write("el_steering_angles = [];\nel_power = [];\n\n")

    # Quick example plot (comment out if not needed)
    f.write("% Example usage in MATLAB:\n")
    f.write("% figure; plot(angles, az_power); grid on;\n")
    f.write("% xlabel('Mechanical Angle (deg)'); ylabel('Power (dBm)');\n")
    f.write("% legend(arrayfun(@(x) sprintf('SA=%g^o', x), az_steering_angles, 'UniformOutput', false));\n")

print(f"MATLAB .m data file written to: {m_path}")




# --- Save measured sweep data to a MATLAB .mat file (variables only) ---
from scipy.io import savemat
import os

matlab_data = {}

# mechanical angles vector
matlab_data["angles"] = np.asarray(angles).reshape(-1, 1)  # Nx1 column vector

# azimuth data
az_keys = sorted(peak_mags_az.keys(), key=float) if peak_mags_az else []
if az_keys:
    az_matrix = np.column_stack([np.asarray(peak_mags_az[k]).ravel() for k in az_keys])  # NxM
    matlab_data["az_steering_angles"] = np.asarray(az_keys).astype(float).reshape(1, -1)    # 1xM
    matlab_data["az_power"] = az_matrix
else:
    matlab_data["az_steering_angles"] = np.zeros((1, 0))
    matlab_data["az_power"] = np.zeros((len(angles), 0))

# elevation data
el_keys = sorted(peak_mags_el.keys(), key=float) if peak_mags_el else []
if el_keys:
    el_matrix = np.column_stack([np.asarray(peak_mags_el[k]).ravel() for k in el_keys])  # NxK
    matlab_data["el_steering_angles"] = np.asarray(el_keys).astype(float).reshape(1, -1)    # 1xK
    matlab_data["el_power"] = el_matrix
else:
    matlab_data["el_steering_angles"] = np.zeros((1, 0))
    matlab_data["el_power"] = np.zeros((len(angles), 0))

# optional: include model results if available
try:
    matlab_data["mechanical_sweep"] = np.asarray(mechanical_sweep)
    matlab_data["azim_results_model"] = np.asarray(azim_results)
    matlab_data["elev_results_model"] = np.asarray(elev_results)
except NameError:
    pass

# optional: include phase/mag dicts if present
try:
    matlab_data["phase_dict"] = np.asarray([phase_dict.get(i+1, np.nan) for i in range(64)])
    matlab_data["mag_dict"] = np.asarray([mag_dict.get(i+1, np.nan) for i in range(64)])
except NameError:
    pass

out_path = "/home/snuc/Desktop/beam_sweeps.mat"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
savemat(out_path, matlab_data, do_compression=True)
print(f"Saved MATLAB .mat data file to: {out_path}")