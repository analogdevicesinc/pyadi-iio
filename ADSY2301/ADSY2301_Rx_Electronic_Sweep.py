# ==========================================================================
# ADSY2301 Rx Electronic Beam Steering Sweep
# --------------------------------------------------------------------------
# PURPOSE
#   Sweeps the receive beam electronically from -60 to +60 degrees (no gimbal
#   or mechanical positioner needed) and plots the combined received-signal
#   magnitude vs. steering angle in real time.
#
#   The script performs the following steps:
#     1. Initialises the ADRV9009 transceiver, TDD engine, and 16 ADAR1000
#        beamformer ICs (64 elements total).
#     2. Runs the DAC / TDD configuration helper (DAC_TDD_Config.py).
#     3. Calibrates per-element gain and phase at boresight.
#     4. Sweeps the beam from SWEEP_MIN to SWEEP_MAX in SWEEP_STEP increments,
#        re-applying calibration corrections at every angle.
#     5. Displays a live Matplotlib plot of magnitude vs. angle.
#     6. Saves the plot (.png) and raw data (.mat) to disk.
#     7. Resets the beam to boresight when finished.
#
# SETUP
#   - Place a horn antenna (or signal source) directly in front of the array
#     at boresight (0 deg azimuth, 0 deg elevation).
#   - Make sure the RF signal source is ON before calibration starts.
#   - No gimbal or mechanical positioner is needed.
#
# HOW TO CUSTOMIZE
#   - SWEEP_MIN / SWEEP_MAX / SWEEP_STEP  — define the angular range and
#     resolution of the sweep.  Valid steering range is roughly -60 to +60 deg.
#   - SWEEP_AXIS  — set to "azimuth" for a horizontal sweep or "elevation"
#     for a vertical sweep.
#   - base_out_dir  — path where output .png and .mat files are written.
#
# OUTPUTS
#   <base_out_dir>/rx_electronic_sweep_<axis>_<timestamp>.png   — plot image
#   <base_out_dir>/rx_electronic_sweep_<axis>_<timestamp>.mat   — MATLAB data
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
 
import os
os.environ['QT_QPA_PLATFORM'] = 'wayland'  # Use Wayland back-end for Qt (Linux)
import subprocess
import sys
import time
from datetime import datetime

import adi                       # pyadi-iio — Analog Devices hardware drivers
from adi.sshfs import sshfs      # SSH helper for remote SoM access
import matplotlib.pyplot as plt  # Live plotting
import numpy as np
from scipy.io import savemat     # Export data in MATLAB .mat format
import ADSY2301 as mr            # ADSY2301 helper module (calibration, capture, etc.)
 
# ──────────────────────────────────────────────────────────────────────────
# USER CONFIGURATION  — Adjust these parameters for your test
# ──────────────────────────────────────────────────────────────────────────
SWEEP_MIN  = -60          # Start angle (degrees)
SWEEP_MAX  = 60           # End angle (degrees)
SWEEP_STEP = 5            # Step size (degrees) — smaller = finer resolution
SWEEP_AXIS = "azimuth"    # "azimuth" (horizontal) or "elevation" (vertical)
url = "ip:192.168.1.1"    # IP address of the ADSY2301 system

# Output folder — .png and .mat files will be saved here
base_out_dir = "/home/snuc/Desktop/rx_electronic_sweep"
os.makedirs(base_out_dir, exist_ok=True)
 
# ==========================================================================
# STEP 1 — Hardware Initialization
# ==========================================================================
# Connect to the ADSY2301 over Ethernet.  The system has:
#   - 16 x ADAR1000 beamformer ICs controlling 64 antenna elements
#   - ADRV9009-ZU11EG transceiver for data conversion
#   - TDDN engine for TDD timing
print(f"Connecting to {url} ...")

ssh = sshfs(address=url, username="root", password="analog")

# -- TDD timing engine --
tddn = adi.tddn(uri=url)
fs_RxIQ = 245.76e6  # RX IQ sample rate (Hz)

# -- ADRV9009-ZU11EG transceiver --
conv = adi.adrv9009_zu11eg(uri=url)
conv._rxadc.set_kernel_buffers_count(1)       # Single kernel buffer for low latency
conv.rx_main_nco_frequencies = [450000000] * 4 # Main NCO at 450 MHz on all 4 channels
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4      # Channel NCOs disabled
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]        # Enable all 4 RX channels
conv.rx_nyquist_zone = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12                  # 4096-sample RX buffer
conv.dds_phases = []
 
# -- Subarray-to-element mapping --
# Each row maps one ADC channel to the 16 antenna elements it serves.
# These mappings are fixed by the ADSY2301 hardware layout.
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],
])
subarray_ref = np.array([1, 33, 37, 5])  # Reference element per subarray (for cal)
adc_map      = np.array([0, 1, 2, 3])    # ADC channel indices
adc_ref      = 0                          # Reference ADC channel
 
# -- ADAR1000 beamformer array (16 ICs × 4 channels = 64 elements) --
sray = adi.adar1000_array(
    uri=url,
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
 
# Phase search space for calibration (-180 to +180 degrees, 1-degree steps)
delay_phases = np.arange(-180, 181, 1)

# Disable all beamformer channels before configuration
mr.disable_stingray_channel(sray)
sray.latch_rx_settings()

# Identify the non-reference ("target") elements that will be phase-aligned
# against their respective reference elements during calibration.
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0], -1))

# Set all 64 elements to RX mode at maximum gain, zero phase
print("Setting all elements to RX mode with max gain...")
for element in sray.elements.values():
    element.rx_attenuator = 0    # No attenuation
    element.rx_gain = 127        # Maximum RX gain
    element.rx_phase = 0         # Zero initial phase
sray.latch_rx_settings()

# Point the beam at boresight (0 deg, 0 deg) to start
sray.steer_rx(azimuth=0, elevation=0)

# Select the internal PLL and set RX gain mode via the XUD control device
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)
PLLselect.attrs["raw"].value = "1"   # Select internal PLL
rxgainmode.attrs["raw"].value = "1"  # Set RX gain mode

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
# STEP 3 — RX Calibration (Gain + Phase)
# ==========================================================================
# The calibration ensures all 64 elements contribute coherently.
#   a) Gain calibration equalises the amplitude across all elements so that
#      no single element dominates or is too weak.
#   b) Phase calibration aligns the phase of every element to a common
#      reference so the array sums constructively at boresight.
input("Place your horn antenna at boresight and make sure the RF source is ON.\n"
      "Press Enter to begin calibration...")

mr.enable_stingray_channel(sray, subarray)

print("\n[CAL] Running gain calibration...")
mr.disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(
    sray, conv, subarray, adc_map, sray.element_map
)
print("[CAL] Gain calibration complete.")

print("[CAL] Running phase calibration...")
cal_ant = mr.find_phase_delay_fixed_ref(
    sray, conv, subarray_ref, adc_ref, delay_phases
)
analog_phase, analog_phase_dict = mr.phase_analog(
    sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant
)
print("[CAL] Phase calibration complete.\n")
 
# ==========================================================================
# STEP 4 — Electronic Beam Steering Sweep
# ==========================================================================
# At each angle the script:
#   1. Commands the ADAR1000 array to steer to the target angle.
#   2. Re-applies the calibration phase corrections.
#   3. Captures IQ data from all 4 ADC channels.
#   4. Computes the coherently combined magnitude (dBm).
#   5. Updates the live plot.
sweep_angles = np.arange(SWEEP_MIN, SWEEP_MAX + 1, SWEEP_STEP)
sweep_mags = np.full(len(sweep_angles), np.nan)

print("=" * 60)
print(f"ELECTRONIC BEAM STEERING SWEEP ({SWEEP_AXIS.upper()})")
print(f"  Range: {SWEEP_MIN} to {SWEEP_MAX} deg, step {SWEEP_STEP} deg")
print(f"  Total positions: {len(sweep_angles)}")
print("=" * 60)

input("Press Enter to start the sweep...")
 
# -- Set up live Matplotlib plot (interactive mode) --
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.ion()
fig, ax = plt.subplots(figsize=(10, 6))
try:
    fig.canvas.manager.window.showMaximized()
except Exception:
    pass
line, = ax.plot([], [], 'o-', linewidth=1.5, markersize=5, color='#2196F3')
ax.axvline(0, color='r', linestyle=':', alpha=0.5, label='Boresight')
ax.set_xlabel(f"Electronic Steering Angle — {SWEEP_AXIS.capitalize()} (degrees)", fontsize=13)
ax.set_ylabel("Combined Magnitude (dBm)", fontsize=13)
ax.set_title(f"ADSY2301 RX Electronic Beam Sweep ({SWEEP_AXIS.capitalize()})", fontsize=15, fontweight='bold')
ax.set_xlim([SWEEP_MIN, SWEEP_MAX])
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)
 
for i, angle in enumerate(sweep_angles):
    # 4a. Steer the beam to the current angle
    if SWEEP_AXIS == "azimuth":
        sray.steer_rx(azimuth=angle, elevation=0)
    else:
        sray.steer_rx(azimuth=0, elevation=angle)
    sray.latch_rx_settings()
    time.sleep(0.1)  # Allow registers to settle

    # 4b. Enable all beamformer channels
    mr.enable_stingray_channel(sray, subarray.flatten().tolist())
    time.sleep(0.3)

    # 4c. Re-apply per-element calibration phase corrections
    #     The correction compensates for the phase that the steer command
    #     added, ensuring the array still sums coherently.
    for element in sray.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.rx_phase = (analog_phase_dict[value] - element.rx_phase) % 360
    sray.latch_rx_settings()
    time.sleep(0.2)
 
    # 4d. Capture IQ data, apply calibration, and compute combined magnitude
    steer_data = np.transpose(np.array(mr.data_capture(conv)))
    steer_data = np.array(steer_data).T
    steer_data = mr.cal_data(steer_data, cal_ant)   # Apply phase/delay correction
    steer_data = np.array(steer_data).T

    combined_data = np.sum(steer_data, axis=1)       # Coherent sum across channels
    sweep_mags[i] = mr.get_analog_mag(combined_data, conv)
 
    print(f"  {SWEEP_AXIS.capitalize()} = {angle:+4d} deg  ->  {sweep_mags[i]:.2f} dBm")
 
    # 4e. Update the live plot with the latest data point
    valid = ~np.isnan(sweep_mags[:i + 1])
    line.set_data(sweep_angles[:i + 1], sweep_mags[:i + 1])
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
fig_path = os.path.join(base_out_dir, f"rx_electronic_sweep_{SWEEP_AXIS}_{timestamp}.png")
fig.savefig(fig_path, dpi=150, bbox_inches='tight')
print(f"Saved figure: {fig_path}")
plt.close(fig)

# ==========================================================================
# STEP 5 — Save Data
# ==========================================================================
# Export the sweep results in MATLAB .mat format for further analysis.
mat_dict = {
    'sweep_angles_deg':     sweep_angles,   # Steering angles (degrees)
    'sweep_magnitudes_dBm': sweep_mags,     # Measured magnitude at each angle
    'sweep_axis':           SWEEP_AXIS,     # "azimuth" or "elevation"
    'sweep_step_deg':       SWEEP_STEP,     # Step size used
    'cal_antenna':          cal_ant,        # Calibration data (for reference)
}
mat_path = os.path.join(base_out_dir, f"rx_electronic_sweep_{SWEEP_AXIS}_{timestamp}.mat")
savemat(mat_path, mat_dict, do_compression=True)
print(f"Saved .mat file: {mat_path}")
 
# ==========================================================================
# STEP 6 — Reset Beam to Boresight
# ==========================================================================
# Return the array to its default state so it is ready for the next test.
sray.steer_rx(azimuth=0, elevation=0)
for element in sray.elements.values():
    element.rx_phase = 0
    element.rx_attenuator = 0
    element.rx_gain = 127
sray.latch_rx_settings()
print("\nBeam reset to boresight (0, 0).")

print("\nElectronic beam sweep complete.")
 
 