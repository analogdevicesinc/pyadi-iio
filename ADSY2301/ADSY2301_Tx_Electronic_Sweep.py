# ==========================================================================
# ADSY2301 Tx Electronic Beam Steering Sweep
# --------------------------------------------------------------------------
# PURPOSE
#   Sweeps the transmit beam electronically from -60 to +60 degrees (no
#   gimbal or mechanical positioner needed) and records measured power vs.
#   steering angle using an external spectrum analyser.
#
#   The script performs the following steps:
#     1. Initialises the ADAR1000 beamformer array, power supplies, and
#        spectrum analyser over VISA / Ethernet.
#     2. Runs the DAC / TDD configuration helper (DAC_TDD_Config.py).
#     3. Loads previously saved TX calibration values from tx_cal_values.json.
#     4. Sweeps the beam from SWEEP_MIN to SWEEP_MAX in SWEEP_STEP increments,
#        reading the measured power from the spectrum analyser at each angle.
#     5. Displays a live Matplotlib plot of power vs. angle.
#     6. Saves the plot (.png) and raw data (.mat) to disk.
#     7. Resets the beam to boresight and disables the PA when finished.
#
# SETUP
#   - Place a receive horn antenna at boresight pointing at the array.
#   - Connect the horn to a spectrum analyser (e.g. Keysight N9000A / CXA).
#   - Connect the PA and bias power supplies.
#   - No gimbal or mechanical positioner is needed.
#
# HOW TO CUSTOMIZE
#   - SWEEP_MIN / SWEEP_MAX / SWEEP_STEP  — define the angular range and
#     resolution of the sweep.  Valid steering range is roughly -60 to +60 deg.
#   - SWEEP_AXIS  — set to "azimuth" for a horizontal sweep or "elevation"
#     for a vertical sweep.
#   - TEST_FREQ_GHZ  — TX frequency; also sets the spectrum analyser centre.
#   - base_out_dir  — path where output .png and .mat files are written.
#
# INSTRUMENT NOTE
#   This script was developed with the following lab instruments:
#     - Keysight N9000A (CXA) spectrum analyser
#     - Keysight E36233A dual-output DC power supply (PA drain)
#     - Keysight N6705B DC power analyser (bias supply)
#   If you use different instruments you will need to replace or adapt the
#   driver imports and VISA resource strings marked with *** INSTRUMENT ***
#   throughout this file.
#
# OUTPUTS
#   <base_out_dir>/tx_electronic_sweep_<axis>_<freq>GHz_<timestamp>.png
#   <base_out_dir>/tx_electronic_sweep_<axis>_<freq>GHz_<timestamp>.mat
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import os
os.environ['QT_QPA_PLATFORM'] = 'wayland'  # Use Wayland back-end for Qt (Linux)
import subprocess
import sys
import time
import json
from datetime import datetime

import adi                       # pyadi-iio — Analog Devices hardware drivers
import matplotlib.pyplot as plt  # Live plotting
import numpy as np
from scipy.io import savemat     # Export data in MATLAB .mat format
import pyvisa                    # VISA instrument communication
import ADSY2301 as mr            # ADSY2301 helper module (calibration, capture, etc.)

# *** INSTRUMENT DRIVERS ***
# The imports below are specific to the lab instruments used in this setup.
# If you use different instruments, replace these with your own drivers or
# use pyvisa SCPI commands directly.
from Drivers import N9000A_Driver as N9000A    # Keysight N9000A / CXA spectrum analyser
from Drivers import N6705B_Driver as N6705B    # Keysight N6705B DC power analyser
from Drivers import E36233A_Driver as E36233A  # Keysight E36233A DC power supply


# ──────────────────────────────────────────────────────────────────────────
# USER CONFIGURATION  — Adjust these parameters for your test
# ──────────────────────────────────────────────────────────────────────────
SWEEP_MIN    = -60        # Start angle (degrees)
SWEEP_MAX    = 60         # End angle (degrees)
SWEEP_STEP   = 1          # Step size (degrees) — smaller = finer resolution
SWEEP_AXIS   = "azimuth"  # "azimuth" (horizontal) or "elevation" (vertical)
TEST_FREQ_GHZ = 10        # TX frequency in GHz (also sets spectrum analyser centre)

# -- Network / VISA addresses --
talise_uri = "ip:192.168.1.1"  # IP address of the ADSY2301 system

# *** INSTRUMENT ADDRESSES ***
# Update the VISA resource strings below to match your own lab instruments.
CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"  # Spectrum analyser (Keysight N9000A / CXA)
E36 = "TCPIP::192.168.1.35::inst0::INSTR"      # PA drain supply  (Keysight E36233A)
N67 = "TCPIP::192.168.1.25::INSTR"             # Bias supply      (Keysight N6705B)

# Output folder — .png and .mat files will be saved here
base_out_dir = "/home/snuc/Desktop/tx_electronic_sweep"
os.makedirs(base_out_dir, exist_ok=True)

# ==========================================================================
# STEP 1 — Hardware Initialization
# ==========================================================================
# Connect to the ADSY2301 and all bench instruments over Ethernet / VISA.
print(f"Connecting to {talise_uri} ...")

rm = pyvisa.ResourceManager()

# *** INSTRUMENT — PA Drain Power Supply ***
# The E36233A supplies the PA drain voltage.  Replace this block if you use
# a different supply.  Key parameters: 22 V, 30 A current limit.
PA_Supplies = E36233A.E36233A(rm, E36)
PA_Supplies.output_off(1)         # Start with output disabled
PA_Supplies.set_voltage(1, 22)    # PA drain voltage
PA_Supplies.set_current(1, 30)    # Current limit

# *** INSTRUMENT — Bias Power Supply ***
# The N6705B provides bias / housekeeping rails.  Replace this block if you
# use a different supply.
Pwr_Supplies = N6705B.N6705B(rm, N67)
Pwr_Supplies.output_off(3)

# *** INSTRUMENT — Spectrum Analyser ***
# The N9000A (CXA) measures the radiated power at each steering angle.
# Replace this block if you use a different spectrum analyser.
SpecAn = N9000A.N9000A(rm, CXA)

# -- ADAR1000 beamformer array (16 ICs × 4 channels = 64 elements) --
dev = adi.adar1000_array(
    uri=talise_uri,
    chip_ids=["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
              "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
              "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
              "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
    element_map=np.array([[1, 9, 17, 25, 33, 41, 49, 57],
                          [2, 10, 18, 26, 34, 42, 50, 58],
                          [3, 11, 19, 27, 35, 43, 51, 59],
                          [4, 12, 20, 28, 36, 44, 52, 60],
                          [5, 13, 21, 29, 37, 45, 53, 61],
                          [6, 14, 22, 30, 38, 46, 54, 62],
                          [7, 15, 23, 31, 39, 47, 55, 63],
                          [8, 16, 24, 32, 40, 48, 56, 64]]),
    device_element_map={
        1:  [9, 10, 2, 1],    3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],  4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],  8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],   11:  [45, 46, 38, 37],
        10: [29, 30, 22, 21], 12:  [61, 62, 54, 53],
        13: [8, 7, 15, 16],   15:  [40, 39, 47, 48],
        14: [24, 23, 31, 32], 16:  [56, 55, 63, 64],
    },
)

# -- TR source and PA bias DAC setup --
# Set all 16 ADAR1000 devices to SPI-controlled TR switching with the bias
# DAC active.  The PA gate bias is set to -4.8 V for both ON and OFF states
# (the TDD engine will gate the actual transmit window).
for device in dev.devices.values():
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

tries = 10  # Retry count — some writes may not stick on the first attempt
for device in dev.devices.values():
    device.bias_dac_mode = "on"
    for channel in device.channels:
        channel.pa_bias_on = -4.8
        if round(channel.pa_bias_on, 1) != -4.8:
            for _ in range(tries):
                if round(channel.pa_bias_on, 1) == -4.8:
                    break
        channel.pa_bias_off = -4.8
        if round(channel.pa_bias_off, 1) != -4.8:
            for _ in range(tries):
                if round(channel.pa_bias_off, 1) == -4.8:
                    break
        dev.latch_tx_settings()

dev.latch_tx_settings()
dev.latch_rx_settings()
print("Initialized BFC Tile")

# Disable PA bias channels until the sweep begins
mr.disable_pa_bias_channel(dev)

print("Hardware initialization complete.\n")

# ==========================================================================
# STEP 2 — DAC / TDD Configuration
# ==========================================================================
# Run the companion script that programs the ADRV9009 transmit DACs and
# the FPGA-based TDD timing engine (pulse timing, duty cycle, TR switching).
print("Running DAC_TDD_Config.py...")
dac_tdd_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DAC_TDD_Config.py")
subprocess.run([sys.executable, dac_tdd_script], check=True)
print("DAC/TDD configuration complete.\n")

# ==========================================================================
# STEP 3 — Load TX Calibration Values
# ==========================================================================
# The TX calibration file (tx_cal_values.json) contains per-element phase,
# gain, and attenuation corrections generated by the TX calibration script.
# These values ensure all 64 elements radiate with matched amplitude and
# phase at boresight.
cal_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tx_cal_values.json")
print(f"Loading TX cal values from: {cal_json_path}")
with open(cal_json_path, "r") as f:
    cal_data = json.load(f)

phase_dict = {int(k): v for k, v in cal_data["phase_dict"].items()}  # Per-element phase (deg)
mag_dict   = {int(k): v for k, v in cal_data["gain_dict"].items()}   # Per-element gain code
atten_dict = {int(k): v for k, v in cal_data["atten_dict"].items()}  # Per-element attenuator

print(f"  Loaded phase_dict for {len(phase_dict)} elements")
print(f"  Loaded gain_dict  for {len(mag_dict)} elements")
print(f"  Loaded atten_dict for {len(atten_dict)} elements")

# Write the calibration corrections into the ADAR1000 registers
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.tx_phase = phase_dict.get(value, 0)
    element.tx_gain  = mag_dict.get(value, 127)
    element.tx_attenuator = atten_dict.get(value, 1)
dev.latch_tx_settings()
print("Applied saved cal values to ADAR1000 hardware.\n")

# Switch TR source to FPGA-controlled (external) and enable bias toggle
# so the TDD engine gates the PA on/off each pulse.
for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"

# ==========================================================================
# STEP 4 — Electronic Beam Steering Sweep
# ==========================================================================
# At each angle the script:
#   1. Commands the ADAR1000 array to steer to the target angle.
#   2. Adds the saved calibration phase on top of the steering phase.
#   3. Reads the measured power from the spectrum analyser.
#   4. Updates the live plot.
active_array = np.array(list(range(1, 65)))  # All 64 elements
sweep_angles = np.arange(SWEEP_MIN, SWEEP_MAX + 1, SWEEP_STEP)
sweep_mags = np.full(len(sweep_angles), np.nan)

print("=" * 60)
print(f"TX ELECTRONIC BEAM STEERING SWEEP ({SWEEP_AXIS.upper()})")
print(f"  Range: {SWEEP_MIN} to {SWEEP_MAX} deg, step {SWEEP_STEP} deg")
print(f"  Total positions: {len(sweep_angles)}")
print(f"  Frequency: {TEST_FREQ_GHZ} GHz")
print("=" * 60)

input("Make sure the receive horn is at boresight and connected to the PXA.\n"
      "Press Enter to start the sweep...")

# *** INSTRUMENT — Enable PA drain supply ***
# Turn on the PA drain voltage and enable all 64 bias channels.
# If you use a different supply, replace the PA_Supplies calls below.
PA_Supplies.output_on(1)
mr.enable_pa_bias_channel(dev, active_array)
time.sleep(3)  # Allow supply to stabilise

# *** INSTRUMENT — Configure Spectrum Analyser ***
# The settings below match the TX calibration script.  If you use a
# different analyser, replace these calls with equivalent SCPI commands
# or your own driver API.
SpecAn.set_to_spec_an_mode()
SpecAn.set_initiate_continuous_sweep('ON')
SpecAn.set_center_freq(TEST_FREQ_GHZ * 1e9)    # Centre at the TX frequency
SpecAn.write("SENS:FREQ:SPAN 10E3")             # 10 kHz span
SpecAn.set_resolution_bandwidth(150e-6)          # Narrow RBW for CW measurement
SpecAn.write("SENS:SWE:TIME 75E-3")             # 75 ms sweep time
SpecAn.set_continuous_peak_search(1, 1)          # Track peak marker
SpecAn.set_attenuation(0)                        # 0 dB input attenuation
SpecAn.set_reference_level(-10)                  # -10 dBm reference level

# -- Set up live Matplotlib plot (interactive mode) --
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.ion()
fig, ax = plt.subplots(figsize=(10, 6))
try:
    fig.canvas.manager.window.showMaximized()
except Exception:
    pass
line, = ax.plot([], [], 'o-', linewidth=1.5, markersize=5, color='#FF5722')
ax.axvline(0, color='r', linestyle=':', alpha=0.5, label='Boresight')
ax.set_xlabel(f"Electronic Steering Angle — {SWEEP_AXIS.capitalize()} (degrees)", fontsize=13)
ax.set_ylabel("Measured Power (dBm)", fontsize=13)
ax.set_title(f"ADSY2301 TX Electronic Beam Sweep ({SWEEP_AXIS.capitalize()}) @ {TEST_FREQ_GHZ} GHz",
             fontsize=15, fontweight='bold')
ax.set_xlim([SWEEP_MIN, SWEEP_MAX])
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

for i, angle in enumerate(sweep_angles):
    # 4a. Steer the beam to the current angle
    if SWEEP_AXIS == "azimuth":
        dev.steer_tx(azimuth=angle, elevation=0)
    else:
        dev.steer_tx(azimuth=0, elevation=angle)
    dev.latch_tx_settings()

    # 4b. Add the saved calibration phase on top of the steering phase
    #     so the array still radiates coherently at the steered angle.
    for element in dev.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.tx_phase = (element.tx_phase + phase_dict[value]) % 360
    dev.latch_tx_settings()
    time.sleep(0.5)  # Allow the new phase settings to propagate

    # 4c. Read the peak power from the spectrum analyser
    # *** INSTRUMENT — If you use a different analyser, replace this call
    #     with the equivalent command to read the marker power (dBm). ***
    sweep_mags[i] = SpecAn.get_marker_power(marker=1)

    print(f"  {SWEEP_AXIS.capitalize()} = {angle:+4d} deg  ->  {sweep_mags[i]:.2f} dBm")

    # 4d. Update the live plot with the latest data point
    line.set_data(sweep_angles[:i + 1], sweep_mags[:i + 1])
    valid = ~np.isnan(sweep_mags[:i + 1])
    if np.any(valid):
        ymin = np.nanmin(sweep_mags[:i + 1]) - 5
        ymax = np.nanmax(sweep_mags[:i + 1]) + 5
        ax.set_ylim([ymin, ymax])
    fig.canvas.draw()
    fig.canvas.flush_events()

plt.ioff()
print("\nSweep complete.\n")
plt.tight_layout()

# Save the final plot as a .png image
fig_path = os.path.join(base_out_dir, f"tx_electronic_sweep_{SWEEP_AXIS}_{TEST_FREQ_GHZ}GHz_{timestamp}.png")
fig.savefig(fig_path, dpi=150, bbox_inches='tight')
print(f"Saved figure: {fig_path}")
plt.close(fig)

# ==========================================================================
# STEP 5 — Save Data
# ==========================================================================
# Export the sweep results in MATLAB .mat format for further analysis.
mat_dict = {
    'sweep_angles_deg':     sweep_angles,    # Steering angles (degrees)
    'sweep_magnitudes_dBm': sweep_mags,      # Measured power at each angle
    'sweep_axis':           SWEEP_AXIS,      # "azimuth" or "elevation"
    'sweep_step_deg':       SWEEP_STEP,      # Step size used
    'frequency_GHz':        TEST_FREQ_GHZ,   # TX frequency
}
mat_path = os.path.join(base_out_dir, f"tx_electronic_sweep_{SWEEP_AXIS}_{TEST_FREQ_GHZ}GHz_{timestamp}.mat")
savemat(mat_path, mat_dict, do_compression=True)
print(f"Saved .mat file: {mat_path}")

# ==========================================================================
# STEP 6 — Reset Beam to Boresight and Disable PA
# ==========================================================================
# Return the array and power supplies to a safe idle state.
dev.steer_tx(azimuth=0, elevation=0)
for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.tx_phase = phase_dict.get(value, 0)
    element.tx_gain  = mag_dict.get(value, 127)
    element.tx_attenuator = atten_dict.get(value, 1)
dev.latch_tx_settings()

# Disable PA bias and turn off the drain supply
mr.disable_pa_bias_channel(dev)
PA_Supplies.output_off(1)  # *** INSTRUMENT — replace if using a different supply ***

print("\nBeam reset to boresight. PA disabled.")
print("\nTX electronic beam sweep complete.")

