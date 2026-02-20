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
# import adar_functions
import re
import json
import os
import pandas as pd
from scipy.special import factorial
from scipy.io import savemat
import sys
from MantaRayTx_Cal import MantaRay as mr
import paramiko
import pyvisa
import paramiko
from Drivers import E8267D_Driver as E8267D
from Drivers import N6705B_Driver as N6705B
from Drivers import E36233A_Driver as E36233A
# Import from Millibox folder (subfolder relative to this file)
from Millibox import mbx_functions as mbx

## Gimbal connection parameters ##
BAUDRATE                    = 57600                  
DEVICENAME                  = "/dev/ttyUSB0"
mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()


## Set up VISA for external instruments ##
rm = pyvisa.ResourceManager()

## Keysight N6705B Power Supply (modular) for Manta Ray Rails ##
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)

# Run the DAC_TDD_Config script
import subprocess
subprocess.run(["/usr/bin/env", "python3", "/home/snuc/pyadi-iio/adi/MantaRay/DAC_TDD_Config.py"], cwd="/home/snuc/pyadi-iio")

SELF_BIASED_LNAs = True
ARRAY_MODE = "rx" 
url = "ip:192.168.1.1"
print("Connecting to", url ,"...")
 
## Set up SSH connection
# url = "local:" if len(sys.argv) == 1 else sys.argv[1]
ssh = sshfs(address=url, username="root", password="analog")

# Setup Talise RX, TDDN Engine & ADAR1000
tddn = adi.tddn(uri = url)
fs_RxIQ = 245.76e6;  #I/Q Data Rate in MSPS
conv = adi.adrv9009_zu11eg(uri = url)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12
conv.dds_phases = []

## Define Subarrays, Reference Channels, and ADC maps ##
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 4
    ])
subarray_ref = np.array([1, 33, 37, 5])  
adc_map      = np.array([0, 1, 2, 3])  # ADC map to subarray
adc_ref      = 0  # ADC reference channel (indexed at 0)

## Setup ADAR1000 Array ##
mray = adi.adar1000_array(
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

# Define delay phases for phase calibration
delay_phases = np.arange(-180,181,1) # sweep phase from -180 to 180 in 1 degree steps.

# Disable all channels initially
mr.disable_stingray_channel(mray)
mray.latch_rx_settings() 

d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d] # analog target channels
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0],-1)) # matrix of subarray target channels to enable/disable wrt reference
 

# Set RX array to desired mode and set ADAR1000s to max gain and 0 phase
if ARRAY_MODE == "rx":
    print("ARRAY_MODE =",ARRAY_MODE,"Setting all devices to rx mode")
    for element in mray.elements.values():
        element.rx_attenuator = 0 # 1: Attentuation on; 0: Attentuation off
        element.rx_gain = 127# 127: Highest gain; 0: Lowest gain
        element.rx_phase = 0 # Set all phases to 0
    mray.latch_rx_settings() # Latch SPI settings to devices

# Set steering angle
mray.steer_rx(azimuth=0, elevation=0) # Broadside 

# Setup ADXUD1AEBZ
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)
cal_ant = mr.find_phase_delay_fixed_ref(mray, conv, subarray_ref, adc_ref, delay_phases)
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"


#########################################################################
#########################################################################
#### Initilization complete; Calibration begins here ####################
#########################################################################
#########################################################################

Pwr_Supplies.output_on(3)
# Enable all elements
mr.enable_stingray_channel(mray,subarray)

# Take data capture
no_cal_data = np.transpose(np.array(mr.data_capture(conv)))

# Gain cal
mr.disable_stingray_channel(mray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(mray, conv, subarray, adc_map, mray.element_map)

# Phase cal
print("Calibrating Phase... Please wait...")
cal_ant = mr.find_phase_delay_fixed_ref(mray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(mray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)

# Take calibrated data capture
mr.enable_stingray_channel(mray)
calibrated_data = np.transpose(np.array(mr.data_capture(conv)))
calibrated_data = np.array(calibrated_data).T
calibrated_data = mr.cal_data(calibrated_data, cal_ant)
calibrated_data = np.array(calibrated_data).T
mr.disable_stingray_channel(mray)

## Plot to check gain and phase calibration ##
plt.ion()   # Turn on interactive mode
fig, axs = plt.subplots(2,1) # Creates a 2x1 grid of subplots

axs[0].plot(no_cal_data.real)
axs[0].set_title('Without Calibration')
axs[0].set_xlabel("Index")
axs[0].set_ylabel("Value")
axs[0].grid(visible=True)
axs[0].set_xlim([100,600])
axs[1].set_ylim([-28000,28000])

axs[1].plot(calibrated_data.real)
axs[1].set_title('With Calibration')
axs[1].set_xlabel("Index")
axs[1].set_ylabel("Value")
axs[1].grid(visible=True)
axs[1].set_ylim([-28000,28000])
axs[1].set_xlim([100,600])

# Adjust layout and display
plt.tight_layout()
plt.draw()
plt.pause(0.001) 
plt.show() 

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

# Sweep parameters
maxsweepangle = 120 # degrees
sweepstep = 1 # degrees
sig_gen_freq_GHz=10 # GHz
steering_angle = 0 # degrees (elevation angle)
gimbal_positions = np.arange(0, (maxsweepangle+1), sweepstep)  # Define gimbal positions from -90 to 90 degrees
single_element_sweep = [] # initialize array to hold single element sweep data
steer_data = []
mag_single_sweep = []
# Create angles array for plotting
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))
# Create array to hold peak magnitudes
peak_mag = np.zeros(len(gimbal_positions))
# Define steering angles to test
steering_angles = [0]

# Steer to desired angle
mray.steer_rx(azimuth=0, elevation=steering_angle) 


for element in mray.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))

    # Assign the calculated steered phase to the element
    element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360

mray.latch_rx_settings()  # Latch SPI settings to devices


# Subarrays dictionary
subarrays = {
    'subarray 1': subarray[0],
    'subarray 2': subarray[3],
    'subarray 3': subarray[2],
    'subarray 4': subarray[1],
}

# Run order
subarray_run_order = ['subarray 1', 'subarray 2', 'subarray 3', 'subarray 4']

##############################################
## Temperature Monitoring Functions ##
##############################################

def get_remote_temps_ssh():
    """Get all ADAR1000 temperatures via SSH."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog", timeout=2)
        
        stdin, stdout, stderr = ssh.exec_command("iio_attr -c adar1000_csb* . | grep 'temp0'")
        output = stdout.read().decode().strip()
        ssh.close()
        
        # Extract all temperature values
        temps = [float(x) for x in re.findall(r"value\s+'([0-9]+(?:\.[0-9]+)?)'", output)]
        return temps
    except Exception as e:
        print(f"Temperature read error: {e}")
        return []

def adc_to_celsius(code):
    """Convert ADAR1000 temp ADC code to degrees Celsius."""
    OFFSET = 135.0
    SLOPE = 0.8  # LSB per °C
    return (code - OFFSET) / SLOPE

def get_adar_temperatures():
    """Get all ADAR1000 temperatures in Celsius."""
    raw_temps = get_remote_temps_ssh()
    if raw_temps:
        temps_c = [adc_to_celsius(t) for t in raw_temps]
        return temps_c
    return []

##############################################
## Step 4: Run Combined RX Sweep (Multiple Samples) ##
###############################################

# Output folder setup
base_out_dir = "/home/snuc/Desktop/repeatability_test_elevation_all64"
os.makedirs(base_out_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("\n" + "="*70)
print("STARTING REPEATABILITY TEST - ALL 64 ELEMENTS")
print("="*70)

# Calculate and plot
mechanical_sweep, elec_steer_angle, azim_results, elev_results, = mr.calc_array_pattern(elec_steer_angle=steering_angle,f_op_GHz=sig_gen_freq_GHz)

# Number of samples for repeatability test
num_samples = 5

# Initialize storage for results across all samples
all_samples_iq = []  # Will store IQ data for each sample
all_samples_powers = []  # Will store power arrays for each sample
all_samples_temp_stats = []  # Will store temperature statistics for each sample

for sample_num in range(1, num_samples + 1):
    print(f"\n{'='*70}")
    print(f"SAMPLE {sample_num}/{num_samples}")
    print(f"{'='*70}")
    
    # Initialize arrays for this sample
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
    peak_mags_az = {angle: np.zeros(len(gimbal_positions)) for angle in steering_angles}
    
    # Initialize temperature tracking
    sample_temps_all = []  # All temperature samples indexed by gimbal position
    
    # Set up dual live plot for this sample (gimbal sweep + temperatures)
    plt.ion()
    fig, (ax_full_array, ax_temps) = plt.subplots(1, 2, figsize=(18, 8))
    mng = fig.canvas.manager
    # Maximize window
    try:
        mng.window.showMaximized()
    except:
        pass

    # Left plot: Gimbal sweep
    line_full_array, = ax_full_array.plot([], [], linestyle='dotted', marker='o', markersize=6, linewidth=2, color='darkblue', label='Full 64-Element Array')
    ax_full_array.set_xlabel("Mechanical Elevation Angle (degrees)", fontsize=12)
    ax_full_array.set_ylabel("Combined RF Input Power (dBm)", fontsize=12)
    ax_full_array.set_title(f"RX Elevation Pattern (Sample {sample_num}) @ {sig_gen_freq_GHz} GHz", fontsize=13, fontweight='bold')
    ax_full_array.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    ax_full_array.grid(True, alpha=0.3)
    ax_full_array.legend(fontsize=11, loc='best')

    # Right plot: Temperatures
    ax_temps.set_xlabel("Sweep Progress (gimbal positions)", fontsize=12)
    ax_temps.set_ylabel("Temperature (°C)", fontsize=12)
    ax_temps.set_title(f"ADAR1000 Temperatures (Sample {sample_num})", fontsize=13, fontweight='bold')
    ax_temps.grid(True, alpha=0.3)
    
    # Storage for temperature lines (for 16 devices + peak + average)
    temp_lines = {}
    colors_16 = plt.cm.tab20(np.linspace(0, 1, 16))
    
    # Initialize lines for each device
    for device_idx in range(16):
        line, = ax_temps.plot([], [], linestyle='-', marker='.', markersize=3, linewidth=1, 
                             color=colors_16[device_idx], alpha=0.7, label=f'Dev {device_idx}')
        temp_lines[f'device_{device_idx}'] = line
    
    # Lines for peak and average
    line_peak, = ax_temps.plot([], [], linestyle='-', marker='*', markersize=10, linewidth=2.5, 
                              color='red', label='Peak Temp')
    line_avg, = ax_temps.plot([], [], linestyle='-', marker='s', markersize=5, linewidth=2, 
                             color='orange', label='Avg Temp')
    temp_lines['peak'] = line_peak
    temp_lines['avg'] = line_avg
    
    ax_temps.legend(fontsize=9, loc='best', ncol=2)

    # Initialize storage for this sample
    sample_iq_data_64 = []
    sample_gimbal_angles_64 = []
    sample_steering_angles_64 = []
    sample_powers_64 = []
    sample_temps_during_sweep = []  # Temperature at each measurement point

    # === Elevation Sweep for this sample ===
    print(f"Starting Elevation Sweep for Sample {sample_num}...")
    gimbal_motor = GIMBAL_V
    mbx.gotoZERO()
    mbx.move(gimbal_motor,-(maxsweepangle/2))

    # Single mechanical sweep for azimuth
    for i in range(len(gimbal_positions)):
        mbx.move(gimbal_motor, sweepstep)
        time.sleep(0.3)
        
        for angle in steering_angles:
            mray.steer_rx(azimuth=0, elevation=angle)
            time.sleep(0.1)
            
            # Enable all 64 elements for full array measurement
            mr.enable_stingray_channel(mray, subarray.flatten().tolist())
            time.sleep(0.3)
            
            # Apply analog phase calibration
            for element in mray.elements.values():
                str_channel = str(element)
                value = int(mr.strip_to_last_two_digits(str_channel))
                element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
            mray.latch_rx_settings()
            time.sleep(0.2)

            steer_data = np.transpose(np.array(mr.data_capture(conv)))
            steer_data = np.array(steer_data).T
            steer_data = mr.cal_data(steer_data, cal_ant)
            steer_data = np.array(steer_data).T

            combined_data = np.sum(steer_data,axis=1)
            peak_mags_az[angle][i] = mr.get_analog_mag(combined_data)
            
            # Read temperatures at this measurement point
            current_temps = get_adar_temperatures()
            sample_temps_during_sweep.append(current_temps)
            
            # Collect IQ data and metadata for combined save
            gimbal_angle = i - (maxsweepangle/2)
            sample_iq_data_64.append(steer_data)
            sample_gimbal_angles_64.append(gimbal_angle)
            sample_steering_angles_64.append(angle)
            sample_powers_64.append(peak_mags_az[angle][i])
            
            # Update live plots
            plot_angles = angles[:i+1]
            plot_power = peak_mags_az[angle][:i+1]
            line_full_array.set_data(plot_angles, plot_power)
            
            # Update temperature plots
            gimbal_progress = np.arange(len(sample_temps_during_sweep))
            
            if len(sample_temps_during_sweep) > 0:
                # Get all device temperatures at each point
                temps_by_device = np.array(sample_temps_during_sweep).T  # Shape: (num_devices, num_measurements)
                
                # Update individual device lines
                for device_idx in range(min(16, temps_by_device.shape[0])):
                    temp_lines[f'device_{device_idx}'].set_data(gimbal_progress, temps_by_device[device_idx])
                
                # Calculate and plot peak and average
                peak_temps = np.max(temps_by_device, axis=0)
                avg_temps = np.mean(temps_by_device, axis=0)
                temp_lines['peak'].set_data(gimbal_progress, peak_temps)
                temp_lines['avg'].set_data(gimbal_progress, avg_temps)
                
                # Auto-scale temperature y-axis
                if len(peak_temps) > 0:
                    y_min = np.min(peak_temps) - 2
                    y_max = np.max(peak_temps) + 2
                    ax_temps.set_ylim([y_min, y_max])
                ax_temps.set_xlim([0, len(sample_temps_during_sweep)])
            
            # Dynamically adjust power y-axis
            valid_data = plot_power[~np.isnan(plot_power)]
            if len(valid_data) > 0:
                y_min = np.min(valid_data) - 5
                y_max = np.max(valid_data) + 5
                ax_full_array.set_ylim([y_min, y_max])
            
            ax_full_array.relim()
            ax_full_array.autoscale_view(scalex=False)
            fig.canvas.draw()
            fig.canvas.flush_events()

    plt.ioff()
    
    # Normalize power data for this sample
    power_normalized = {}
    for angle in steering_angles:
        power_data = peak_mags_az[angle]
        max_power = np.max(power_data)
        # Normalize to 0 dB at the peak
        power_normalized[angle] = power_data - max_power
    
    # Save this sample's IQ data and temperature data to .mat file
    sample_iq_mat_path = os.path.join(
        base_out_dir,
        f"sample_{sample_num:02d}_elevation_raw_iq_full_64element_{sig_gen_freq_GHz}GHz_{timestamp}.mat"
    )
    
    # Calculate temperature statistics
    temps_array = np.array(sample_temps_during_sweep).T  # Shape: (num_devices, num_measurements)
    peak_temps_array = np.max(temps_array, axis=0)
    avg_temps_array = np.mean(temps_array, axis=0)
    
    sample_iq_dict = {
        "all_iq_data": np.array(sample_iq_data_64),
        "gimbal_angles_deg": np.array(sample_gimbal_angles_64),
        "steering_angles_deg": np.array(sample_steering_angles_64),
        "power_dBm": np.array(sample_powers_64),
        "power_normalized_dB": power_normalized[steering_angles[0]],
        "mechanical_angles_deg": angles,
        "frequency_GHz": sig_gen_freq_GHz,
        "description": f"Full 64-element combined RX elevation sweep from -60 to +60 degrees with temperature monitoring (Sample {sample_num})",
        "num_sweeps": len(sample_iq_data_64),
        "sample_number": sample_num,
        "temperature_all_devices": temps_array,  # Shape: (16, num_measurements)
        "temperature_peak": peak_temps_array,
        "temperature_avg": avg_temps_array,
    }
    savemat(sample_iq_mat_path, sample_iq_dict, do_compression=True)
    print(f"Saved Sample {sample_num} IQ and temperature data to: {sample_iq_mat_path}")
    if len(peak_temps_array) > 0:
        print(f"  Temperature range: {np.min(peak_temps_array):.1f}°C to {np.max(peak_temps_array):.1f}°C")
    
    # Save this sample's power plot
    sample_png_path = os.path.join(
        base_out_dir,
        f"sample_{sample_num:02d}_elevation_pattern_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )
    
    # Create and save the figure
    fig_save, ax_save = plt.subplots(figsize=(12, 7))
    for angle in steering_angles:
        ax_save.plot(angles, peak_mags_az[angle], 
                     linestyle='dotted', marker='o', markersize=5, linewidth=2, label=f'Sample {sample_num}')
    ax_save.set_title(f'RX Elevation Pattern - Full 64 Elements (Sample {sample_num}) @ {sig_gen_freq_GHz} GHz', fontsize=14, fontweight='bold')
    ax_save.set_xlabel('Mechanical Elevation Angle (degrees)', fontsize=12)
    ax_save.set_ylabel('Combined RF Input Power (dBm)', fontsize=12)
    ax_save.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    ax_save.grid(True, alpha=0.3)
    ax_save.legend(fontsize=11)
    fig_save.tight_layout()
    plt.savefig(sample_png_path, dpi=150)
    plt.close(fig_save)
    print(f"Saved Sample {sample_num} plot to: {sample_png_path}")
    
    # Save the normalized plot for this sample
    normalized_png_path = os.path.join(
        base_out_dir,
        f"sample_{sample_num:02d}_elevation_pattern_NORMALIZED_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )
    
    fig_norm, ax_norm = plt.subplots(figsize=(12, 7))
    for angle in steering_angles:
        ax_norm.plot(angles, power_normalized[angle], 
                     linestyle='dotted', marker='o', markersize=5, linewidth=2, label=f'Sample {sample_num}')
    ax_norm.set_title(f'RX Elevation Pattern NORMALIZED - Full 64 Elements (Sample {sample_num}) @ {sig_gen_freq_GHz} GHz', 
                      fontsize=14, fontweight='bold')
    ax_norm.set_xlabel('Mechanical Azimuth Angle (degrees)', fontsize=12)
    ax_norm.set_ylabel('Normalized Power (dB, 0 dB at peak)', fontsize=12)
    ax_norm.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
    ax_norm.grid(True, alpha=0.3)
    ax_norm.legend(fontsize=11)
    fig_norm.tight_layout()
    plt.savefig(normalized_png_path, dpi=150)
    plt.close(fig_norm)
    print(f"Saved Sample {sample_num} NORMALIZED plot to: {normalized_png_path}")
    
    # Save the dual-plot (gimbal + temperature) as well
    dual_plot_path = os.path.join(
        base_out_dir,
        f"sample_{sample_num:02d}_elevation_gimbal_and_temperature_{sig_gen_freq_GHz}GHz_{timestamp}.png"
    )
    fig.savefig(dual_plot_path, dpi=150)
    plt.close(fig)
    print(f"Saved Sample {sample_num} dual-plot (gimbal+temp) to: {dual_plot_path}")
    
    # Store this sample's results for overlay plot later
    all_samples_iq.append(sample_iq_data_64)
    all_samples_powers.append(peak_mags_az)
    
    # Store temperature statistics for this sample
    if len(peak_temps_array) > 0:
        peak_avg_temp = np.mean(peak_temps_array)
        all_samples_temp_stats.append(peak_avg_temp)
    else:
        all_samples_temp_stats.append(0.0)
    
    mbx.gotoZERO()

# Store normalized powers for all samples
all_samples_powers_normalized = []  # Will be populated during overlay creation

print(f"\n{'='*70}")
print("ALL SAMPLES COMPLETED")
print(f"{'='*70}")

# Create overlay plot with all samples
fig_overlay, ax_overlay = plt.subplots(figsize=(14, 8))
colors = plt.cm.tab10(np.linspace(0, 1, num_samples))

for sample_idx, sample_powers in enumerate(all_samples_powers, 1):
    # Get temperature info for this sample
    peak_avg_temp = all_samples_temp_stats[sample_idx - 1]
    temp_label = f'Sweep {sample_idx}: Peak Avg Temp {peak_avg_temp:.1f}°C'
    
    for angle in steering_angles:
        ax_overlay.plot(angles, sample_powers[angle], 
                       linestyle='dotted', marker='o', markersize=4, linewidth=1.5, 
                       label=temp_label, color=colors[sample_idx - 1], alpha=0.8)

ax_overlay.set_title(f'RX Elevation Pattern Overlay - Full 64 Elements (All {num_samples} Samples) @ {sig_gen_freq_GHz} GHz', 
                     fontsize=14, fontweight='bold')
ax_overlay.set_xlabel('Mechanical Elevation Angle (degrees)', fontsize=12)
ax_overlay.set_ylabel('Combined RF Input Power (dBm)', fontsize=12)
ax_overlay.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
ax_overlay.grid(True, alpha=0.3)
ax_overlay.legend(fontsize=10, loc='best', ncol=2)
fig_overlay.tight_layout()

overlay_png_path = os.path.join(base_out_dir, f"all_samples_elevation_overlay_{sig_gen_freq_GHz}GHz_{timestamp}.png")
plt.savefig(overlay_png_path, dpi=150)
plt.close(fig_overlay)
print(f"\nSaved overlay plot to: {overlay_png_path}")

# Create normalized overlay plot with all samples
fig_overlay_norm, ax_overlay_norm = plt.subplots(figsize=(14, 8))

for sample_idx, sample_powers in enumerate(all_samples_powers, 1):
    # Get temperature info for this sample
    peak_avg_temp = all_samples_temp_stats[sample_idx - 1]
    temp_label = f'Sweep {sample_idx}: Peak Avg Temp {peak_avg_temp:.1f}°C'
    
    for angle in steering_angles:
        # Normalize each sweep
        power_data = sample_powers[angle]
        max_power = np.max(power_data)
        power_norm = power_data - max_power
        
        ax_overlay_norm.plot(angles, power_norm, 
                            linestyle='dotted', marker='o', markersize=4, linewidth=1.5, 
                            label=temp_label, color=colors[sample_idx - 1], alpha=0.8)

ax_overlay_norm.set_title(f'RX Elevation Pattern Overlay NORMALIZED - Full 64 Elements (All {num_samples} Samples) @ {sig_gen_freq_GHz} GHz', 
                          fontsize=14, fontweight='bold')
ax_overlay_norm.set_xlabel('Mechanical Elevation Angle (degrees)', fontsize=12)
ax_overlay_norm.set_ylabel('Normalized Power (dB, 0 dB at peak)', fontsize=12)
ax_overlay_norm.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
ax_overlay_norm.grid(True, alpha=0.3)
ax_overlay_norm.legend(fontsize=10, loc='best', ncol=2)
fig_overlay_norm.tight_layout()

overlay_norm_png_path = os.path.join(base_out_dir, f"all_samples_elevation_overlay_NORMALIZED_{sig_gen_freq_GHz}GHz_{timestamp}.png")
plt.savefig(overlay_norm_png_path, dpi=150)
plt.close(fig_overlay_norm)
print(f"Saved NORMALIZED overlay plot to: {overlay_norm_png_path}")


# Create combined .mat file with all samples
all_samples_mat_path = os.path.join(base_out_dir, f"all_samples_combined_elevation_64element_{sig_gen_freq_GHz}GHz_{timestamp}.mat")
all_samples_dict = {
    "all_samples_power_dBm": np.array([sp[0] for sp in all_samples_powers]),  # Shape: (num_samples, len(angles))
    "mechanical_angles_deg": angles,
    "frequency_GHz": sig_gen_freq_GHz,
    "num_samples": num_samples,
    "num_elements": 64,
    "description": "Repeatability test - all 64 elements combined, elevation sweep, multiple samples",
    "steering_elevation_deg": 0,
}
savemat(all_samples_mat_path, all_samples_dict, do_compression=True)
print(f"Saved combined samples .mat file to: {all_samples_mat_path}")

print(f"\nAll results saved to: {base_out_dir}")
print("\nRepeatability test complete!")

# Turn off the 5.7V rail
print("\nShutting down power supplies...")
Pwr_Supplies.output_off(3)
print("5.7V rail turned off.")


# ======================================================================
# MONOPULSE POST-PROCESSING (Σ / Δ) — CORRECT ELEMENT-SPACE VERSION
# ======================================================================

import glob
from scipy.io import loadmat

def db_norm(x):
    mag = np.abs(x)
    mag /= (np.max(mag) + 1e-12)
    return 20*np.log10(mag + 1e-12)

print("\n" + "="*70)
print("MONOPULSE POST-PROCESSING (ELEMENT-SPACE VERIFIED)")
print("="*70)

mat_files = sorted(glob.glob(
    os.path.join(base_out_dir, "sample_*_elevation_raw_iq_full_64element_*.mat")
))

fig, ax = plt.subplots(figsize=(13, 8))
colors = plt.cm.tab10(np.linspace(0, 1, len(mat_files)))

for idx, mf in enumerate(mat_files):
    D = loadmat(mf)

    all_iq = D["all_iq_data"]      # MATLAB cell array
    mech_angles = D["mechanical_angles_deg"].squeeze()

    num_angles = all_iq.shape[0]

    sigma = np.zeros(num_angles, dtype=np.complex128)
    delta = np.zeros(num_angles, dtype=np.complex128)

    for k in range(num_angles):
        # ---- Extract ONE angle snapshot ----
        steer_data = np.atleast_2d(all_iq[k, 0])

        # ---- HARD ASSERTIONS (this is the fix) ----
        if steer_data.shape[0] != 64:
            raise RuntimeError(
                f"Expected 64 elements, got {steer_data.shape[0]} at angle index {k}"
            )

        # ---- Coherent sum over FAST-TIME ONLY ----
        elem_acc = np.sum(steer_data, axis=1)   # shape: [64]

        # ---- TRUE MONOPULSE FORMATION ----
        left  = np.sum(elem_acc[0:32])
        right = np.sum(elem_acc[32:64])

        sigma[k] = left + right
        delta[k] = left - right

    # ---- Normalize ----
    sigma_db = db_norm(sigma)
    delta_db = db_norm(delta)

    # ---- Overlay plots ----
    ax.plot(
        mech_angles,
        sigma_db,
        color=colors[idx],
        linewidth=2.5,
        label=f"Σ Sample {idx+1}"
    )

    ax.plot(
        mech_angles,
        delta_db,
        color=colors[idx],
        linestyle="--",
        linewidth=2.5,
        label=f"Δ Sample {idx+1}"
    )

ax.set_title(
    "Monopulse Σ / Δ Overlay (ELEMENT-SPACE CORRECT)",
    fontsize=15,
    fontweight="bold"
)
ax.set_xlabel("Mechanical Elevation Angle (deg)", fontsize=12)
ax.set_ylabel("Magnitude (dB)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10, ncol=2)
ax.set_ylim(-50, 1)

fig.tight_layout()

out_png = os.path.join(
    base_out_dir,
    f"MONOPULSE_SUM_DELTA_OVERLAY_{sig_gen_freq_GHz}GHz_{timestamp}.png"
)

fig.savefig(out_png, dpi=150)
plt.close(fig)

print(f"\nSaved corrected monopulse plot:\n  {out_png}")
print("\nMonopulse processing COMPLETE.")
