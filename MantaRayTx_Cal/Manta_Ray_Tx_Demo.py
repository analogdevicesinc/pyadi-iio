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

## Enter desired array shape here: "4x4", "6x6", "8x8", or "outer" ##
desired_array_shape = "8x8"

if desired_array_shape == "4x4":
    active_array = array_shapes[0]

elif desired_array_shape == "6x6":
    active_array = array_shapes[1]

elif desired_array_shape == "8x8":
    active_array = array_shapes[2]

elif desired_array_shape == "outer":
    active_array = array_shapes[3]

elif desired_array_shape == "subarray 4":
    active_array = array_shapes[4]

elif desired_array_shape == "subarray 3":
    active_array = array_shapes[5]

elif desired_array_shape == "subarray 2":
    active_array = array_shapes[6]

elif desired_array_shape == "subarray 1":
    active_array = array_shapes[7]

elif desired_array_shape == "single":
    active_array = array_shapes[8]



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


# active_array = np.array(active_array)
# phase_dict_ref = active_array.transpose().flatten()
# phase_dict = mr.create_dict(phase_dict_ref, np.zeros(16))
# mag_dict_ref = active_array.transpose().flatten()
# mag_dict = mr.create_dict(mag_dict_ref, np.zeros(16))
        

active_array = np.array(active_array)
phase_dict_ref = active_array.transpose().flatten()
phase_dict = mr.create_dict(phase_dict_ref, np.zeros(64))
mag_dict_ref = active_array.transpose().flatten()
mag_dict = mr.create_dict(mag_dict_ref, np.zeros(64))


# Get Phase Data from ADAR1000 
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    phase_dict[value] = element.tx_phase
    mag_dict[value] = element.tx_gain

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

# # === Azimuth Sweep ===
print("Starting Azimuth Sweep...")
gimbal_motor = GIMBAL_H
mbx.gotoZERO()
mbx.move(gimbal_motor,-(maxsweepangle/2))
mr.enable_pa_bias_channel(dev, active_array)
time.sleep(3)


# Prepare interactive plot for real-time updates


# ORIGINAL CODE BELOW:
plt.ion()
fig, ax = plt.subplots(figsize=(10, 6))


ax.set_title('Azimuth Pattern (real-time)')
ax.set_xlabel('Mechanical Azimuth Angle (degrees)')
ax.set_ylabel('Combined RF Input Power (dBm)')
ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
ax.grid(True)
ax.legend(loc='best')

# Single mechanical sweep for azimuth with real-time plotting
mbx.gotoZERO()
mbx.move(gimbal_motor, -(maxsweepangle/2))
mr.enable_pa_bias_channel(dev, active_array)
time.sleep(3)

for i in range(len(gimbal_positions)):
    for steering_angle in steering_angles:
        dev.steer_tx(azimuth=steering_angle, elevation=0)
        dev.latch_tx_settings()
        # Apply analog phase calibration
        for element in dev.elements.values():
            str_channel = str(element)
            value = int(mr.strip_to_last_two_digits(str_channel))
            element.tx_phase = (phase_dict[value] - element.tx_phase) % 360

        dev.latch_tx_settings()
        time.sleep(0.5)
        peak_mags_az[steering_angle][i] = SpecAn.get_marker_power(marker=1)

    # update real-time plot after this mechanical position
    ax.clear()
    x = angles[: i + 1]
    for sa in steering_angles:
        y = peak_mags_az[sa][: i + 1]
        ax.plot(x, y, linestyle='dotted', marker='o', markersize=4, label=f'Measured SA={sa}°')

    ax.set_title('Azimuth Pattern (real-time)')
    ax.set_xlabel('Mechanical Azimuth Angle (degrees)')
    ax.set_ylabel('Combined RF Input Power (dBm)')
    ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    
    # Dynamically adjust y limits with ±10 dBm margin
    all_data = np.concatenate([peak_mags_az[sa][: i + 1] for sa in steering_angles])
    if len(all_data) > 0:
        y_min = np.nanmin(all_data) - 10
        y_max = np.nanmax(all_data) + 10
        ax.set_ylim(y_min, y_max)
    
    ax.grid(True)
    ax.legend(loc='best')
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)   # small pause to allow GUI event loop to update

    mbx.move(gimbal_motor, sweepstep)

# finish sweep
mbx.gotoZERO()
mr.disable_pa_bias_channel(dev, active_array)

#Set Phases back to calibrated phases
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.tx_phase = (phase_dict[value])

# turn off interactive mode (optional)
plt.ioff()
# ...existing code...


a=1
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