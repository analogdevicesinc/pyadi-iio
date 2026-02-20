# Manta Ray 64 Element RX Electronic Steering Array Beam Pattern Test
# Based on Manta_Ray_RX_Demo calibration approach
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import os
os.environ['QT_QPA_PLATFORM'] = 'wayland'
import matplotlib
import time
from datetime import datetime
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import savemat
import sys
sys.path.insert(0, '/home/snuc/pyadi-iio/MantaRayTx_Cal')
import MantaRay as mr
import mbx_functions as mbx
import pyvisa
from N6705B_Driver import N6705B

##############################################
## Initialize System
##############################################

BAUDRATE = 57600
DEVICENAME = "/dev/ttyUSB0"
mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

# Power supplies
rm = pyvisa.ResourceManager()
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B(rm, N67)

##############################################
## Setup RX Array
##############################################

url = "ip:192.168.1.1"
print(f"Connecting to {url}...")

ssh = sshfs(address=url, username="root", password="analog")

# Setup Talise RX
tddn = adi.tddn(uri=url)
fs_RxIQ = 245.76e6
conv = adi.adrv9009_zu11eg(uri=url)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12

# Define subarrays
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],      # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64], # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],     # subarray 4
])
subarray_ref = np.array([1, 33, 37, 5])
adc_map = np.array([0, 1, 2, 3])
adc_ref = 0

# Setup ADAR1000 Array
sray = adi.adar1000_array(
    uri=url,
    chip_ids=["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
              "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
              "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
              "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
    element_map=np.array([[1, 9,  17, 25, 33, 41, 49, 57],
                          [2, 10, 18, 26, 34, 42, 50, 58],
                          [3, 11, 19, 27, 35, 43, 51, 59],
                          [4, 12, 20, 28, 36, 44, 52, 60],
                          [5, 13, 21, 29, 37, 45, 53, 61],
                          [6, 14, 22, 30, 38, 46, 54, 62],
                          [7, 15, 23, 31, 39, 47, 55, 63],
                          [8, 16, 24, 32, 40, 48, 56, 64]]),
    device_element_map={
        1:  [9, 10, 2, 1],      3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],   4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],     7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],   8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],   12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],     15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],   16: [56, 55, 63, 64],
    },
)

# Initialize array
delay_phases = np.arange(-180, 181, 1)
mr.disable_stingray_channel(sray)
sray.latch_rx_settings()

d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0], -1))

# Set RX array to desired mode
print("Setting all devices to RX mode")
for element in sray.elements.values():
    element.rx_attenuator = 0
    element.rx_gain = 127
    element.rx_phase = 0
sray.latch_rx_settings()

sray.steer_rx(azimuth=0, elevation=0)

ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"

print("\nMake sure RF is on! Press Enter to continue...")
input()

##############################################
## Calibration
##############################################

print("\n" + "="*70)
print("STARTING RX ARRAY CALIBRATION")
print("="*70)

# Enable all for calibration BEFORE trying to capture data
mr.enable_stingray_channel(sray, subarray.flatten().tolist())
time.sleep(1)

try:
    print("Capturing calibration data...")
    cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
except TimeoutError as e:
    print(f"Timeout during calibration: {e}")
    print("Attempting to reconnect and retry...")
    time.sleep(2)
    mr.enable_stingray_channel(sray, subarray.flatten().tolist())
    time.sleep(1)
    cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)

print("Performing Gain Calibration...")
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(sray, conv, subarray, adc_map, sray.element_map)

print("Calibrating Phase... Please wait...")
analog_phase, analog_phase_dict = mr.phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)

print("RX Array Calibration Complete!")
print("="*70)

mr.disable_stingray_channel(sray)

##############################################
## Gimbal and Sweep Parameters
##############################################

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

sig_gen_freq_GHz = 10
steering_angle = 0
maxsweepangle = 120
sweepstep = 1
gimbal_motor = GIMBAL_H
gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))

steering_angles = [0]

subarrays = {
    'subarray 1': subarray[0],
    'subarray 2': subarray[1],
    'subarray 3': subarray[2],
    'subarray 4': subarray[3],
}

subarray_run_order = ['subarray 1', 'subarray 2', 'subarray 3', 'subarray 4']

##############################################
## Output Setup
##############################################

base_out_dir = "/home/snuc/Desktop/rx_subarray_plots"
os.makedirs(base_out_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
all_subarray_results = {}

print("\n" + "="*70)
print("STARTING RX BEAM PATTERN TEST FOR ALL SUBARRAYS")
print("="*70)

##############################################
## Run Sweeps for Each Subarray
##############################################

for subarray_name in subarray_run_order:
    print(f"\n{'='*70}")
    print(f"--- Testing {subarray_name} ---")
    print(f"{'='*70}")
    sys.stdout.flush()
    
    # Create subfolder
    sub_dir = os.path.join(base_out_dir, subarray_name.replace(' ', '_'))
    os.makedirs(sub_dir, exist_ok=True)

    active_elements = subarrays[subarray_name].tolist()
    print(f"Active elements: {active_elements}")
    sys.stdout.flush()
    
    # Enable only this subarray
    mr.enable_stingray_channel(sray, active_elements)
    time.sleep(1)

    # Storage for this subarray
    peak_mags_az = {angle: np.full(len(gimbal_positions), np.nan) for angle in steering_angles}

    # Reset gimbal to start position
    print("Resetting gimbal...")
    sys.stdout.flush()
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle/2))
    time.sleep(0.5)
    print("Starting gimbal sweep...")
    sys.stdout.flush()

    # Sweep gimbal and collect data
    for i in range(len(gimbal_positions)):
        for steering_angle in steering_angles:
            # Steer RX
            sray.steer_rx(azimuth=steering_angle, elevation=0)
            
            # Apply phase calibration
            for element in sray.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                if value in set(active_elements):
                    element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
            sray.latch_rx_settings()

            time.sleep(0.3)
            
            # Capture RX data
            data = None
            try:
                data = np.transpose(np.array(mr.data_capture(conv)))
                data = np.array(data).T
                data = mr.cal_data(data, cal_ant)
                data = np.array(data).T
                
                # Combine all 4 ADC channels (like in Manta_Ray_RX_Demo)
                combined_data = data[:, 0] + data[:, 1] + data[:, 2] + data[:, 3]
                power_val = mr.get_analog_mag(combined_data)
                peak_mags_az[steering_angle][i] = power_val
                
                output_str = f"{subarray_name} - Gimbal {i}/{len(gimbal_positions)-1} (Angle {angles[i]:6.1f}°): {power_val:8.2f} dBm"
                print(output_str)
                sys.stdout.flush()
                
            except Exception as e:
                print(f"ERROR at gimbal position {i}: {str(e)}")
                sys.stdout.flush()
                peak_mags_az[steering_angle][i] = np.nan

        # Move gimbal to next position
        if i < len(gimbal_positions) - 1:  # Don't move on last iteration
            mbx.move(gimbal_motor, sweepstep)
            time.sleep(0.2)

    # Return gimbal home
    mbx.gotoZERO()
    mr.disable_stingray_channel(sray)
    
    all_subarray_results[subarray_name] = peak_mags_az

    # Save MAT file
    for steering_angle in steering_angles:
        mat_path = os.path.join(
            sub_dir,
            f"rx_power_vs_angle_{subarray_name.replace(' ', '_')}_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.mat"
        )
    
        mdict = {
            "angles_deg": angles.reshape(-1, 1),
            "power_dBm": peak_mags_az[steering_angle].reshape(-1, 1),
            "steering_angle_deg": steering_angle,
            "frequency_GHz": sig_gen_freq_GHz,
            "subarray": subarray_name,
        }
    
        savemat(mat_path, mdict, do_compression=True)
        print(f"Saved {subarray_name} RX data to {mat_path}")

    # Save PNG plot
    for steering_angle in steering_angles:
        plt.figure(figsize=(12, 8))
        plt.plot(angles, peak_mags_az[steering_angle],
                linestyle="dotted", marker="o", markersize=5, linewidth=2)
        plt.title(f"RX Azimuth Pattern - {subarray_name} @ {sig_gen_freq_GHz} GHz (SA={steering_angle}°)", fontsize=14, fontweight='bold')
        plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=12)
        plt.ylabel("Combined RF Input Power (dBm)", fontsize=12)
        plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(sub_dir, f"rx_azimuth_{subarray_name.replace(' ', '_')}_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.png"), dpi=150)
        plt.close()

# Create overview figure
try:
    if 0 in steering_angles:
        fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
        for ax, name in zip(axs.ravel(), subarray_run_order):
            y = all_subarray_results[name][0]
            ax.plot(angles, y, linestyle="dotted", marker="o", markersize=4, linewidth=2)
            ax.set_title(f"{name} @ {sig_gen_freq_GHz} GHz", fontsize=12)
            ax.grid(True)
        fig.suptitle(f"RX Azimuth Pattern Overview (SA=0°) @ {sig_gen_freq_GHz} GHz", fontsize=16, fontweight='bold')
        for ax in axs[-1, :]:
            ax.set_xlabel("Mechanical Azimuth Angle (degrees)")
        for ax in axs[:, 0]:
            ax.set_ylabel("Combined RF Input Power (dBm)")
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(os.path.join(base_out_dir, f"rx_azimuth_overview_SA0_{sig_gen_freq_GHz}GHz_{timestamp}.png"), dpi=150)
        plt.close(fig)
except Exception as e:
    print(f"Overview plot generation skipped: {e}")

# Create combined overlay plot with all subarrays on one graph
try:
    colors = ['blue', 'red', 'green', 'purple']
    markers = ['o', 's', '^', 'D']
    
    for steering_angle in steering_angles:
        plt.figure(figsize=(14, 8))
        
        for idx, name in enumerate(subarray_run_order):
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
        
        plt.title(f"RX Azimuth Pattern - All Subarrays @ {sig_gen_freq_GHz} GHz (SA={steering_angle}°)", fontsize=16, fontweight='bold')
        plt.xlabel("Mechanical Azimuth Angle (degrees)", fontsize=14)
        plt.ylabel("Combined RF Input Power (dBm)", fontsize=14)
        plt.xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12, loc='best')
        plt.tight_layout()
        
        combined_plot_path = os.path.join(base_out_dir, f"rx_azimuth_combined_all_subarrays_SA{steering_angle}deg_{sig_gen_freq_GHz}GHz_{timestamp}.png")
        plt.savefig(combined_plot_path, dpi=150)
        plt.close()
        print(f"Saved combined RX plot to {combined_plot_path}")
        
except Exception as e:
    print(f"Combined overlay plot generation failed: {e}")

print("\n" + "="*70)
print("RX BEAM PATTERN TEST COMPLETE")
print("="*70)
print(f"\nResults saved to {base_out_dir}")
