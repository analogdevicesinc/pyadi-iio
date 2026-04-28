# ==========================================================================
# ADSY2301 Rx Beam Steering Demo
# --------------------------------------------------------------------------
# PURPOSE
#   Demonstrates electronic beam steering on the ADSY2301 64-element phased
#   array.  A horn antenna (or any far-field source) is placed at boresight.
#   The script:
#     1. Initializes the hardware and calibrates gain + phase.
#     2. Captures a baseline measurement with the beam pointed at boresight
#        (azimuth = 0 deg).
#     3. Steers the beam to +30 deg azimuth and captures again.
#     4. Prints the combined magnitude of all 4 ADC channels at each angle.
#
# SETUP
#   - Place a horn antenna (or signal source) directly in front of the array
#     at boresight (0 deg azimuth, 0 deg elevation).
#   - Make sure the RF signal source is ON before calibration starts.
#   - No gimbal or mechanical positioner is needed.
#
# HOW TO CUSTOMIZE
#   - Change STEER_ANGLE below to steer to a different angle.
#   - The sray.steer_rx(azimuth, elevation) call is the main steering hook:
#       azimuth:   horizontal steer angle in degrees (negative = left)
#       elevation: vertical steer angle in degrees
#     Valid range is roughly -60 to +60 degrees in each axis.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
 
import adi
from adi.sshfs import sshfs
import numpy as np
import ADSY2301 as mr

# ──────────────────────────────────────────────────────────────────────────
# USER CONFIGURATION  — Adjust these parameters for your test
# ──────────────────────────────────────────────────────────────────────────
STEER_ANGLE = 30        # Azimuth angle (degrees) to steer away from boresight
url = "ip:192.168.1.1"  # IP address of the ADSY2301 system
 
# ==========================================================================
# STEP 1 — Hardware Initialization
# ==========================================================================
# Connect to the ADSY2301 over Ethernet.  The system has:
#   - 16 x ADAR1000 beamformer ICs controlling 64 antenna elements
#   - ADRV9009-ZU11EG transceiver for data conversion
#   - TDDN engine for TDD timing (not used in this RX-only demo)
print(f"Connecting to {url} ...")
 
ssh = sshfs(address=url, username="root", password="analog")
 
tddn = adi.tddn(uri=url)
fs_RxIQ = 245.76e6  # RX IQ sample rate in Hz
 
# Configure the ADRV9009 transceiver for receive
conv = adi.adrv9009_zu11eg(uri=url)
conv._rxadc.set_kernel_buffers_count(1)
conv.rx_main_nco_frequencies = [450000000] * 4   # Main NCO at 450 MHz per channel
conv.rx_main_nco_phases = [0] * 4
conv.rx_channel_nco_frequencies = [0] * 4
conv.rx_channel_nco_phases = [0] * 4
conv.rx_enabled_channels = [0, 1, 2, 3]          # Enable all 4 RX channels
conv.rx_nyquist_zone = ["odd"] * 4
conv.rx_buffer_size = 2 ** 12                     # 4096 samples per capture
conv.dds_phases = []
 
# ── Subarray / channel mapping ──
# The 64 elements are split into 4 subarrays of 16 elements each.
# Each subarray feeds one ADC channel on the transceiver.
subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28],
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60],
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32],
])
subarray_ref = np.array([1, 33, 37, 5])  # One reference element per subarray
adc_map      = np.array([0, 1, 2, 3])    # ADC channel index for each subarray
adc_ref      = 0                          # ADC channel used as the phase reference
 
# ── ADAR1000 array object ──
# This maps physical ADAR1000 chip-selects to logical device/element numbers.
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
 
# Phase search range for calibration (1-degree resolution over full circle)
delay_phases = np.arange(-180, 181, 1)
 
# Set all channels to a known-off state before configuring
mr.disable_stingray_channel(sray)
sray.latch_rx_settings()
 
# Identify non-reference elements (these are the ones we calibrate against the ref)
d = ~np.isin(subarray, subarray_ref)
subarray_targ = subarray[d]
subarray_targ = np.reshape(subarray_targ, (subarray.shape[0], -1))
 
# Set all 64 elements to receive mode with max gain, zero phase offset
print("Setting all elements to RX mode with max gain...")
for element in sray.elements.values():
    element.rx_attenuator = 0
    element.rx_gain = 127
    element.rx_phase = 0
sray.latch_rx_settings()
 
# Point the beam at boresight (0, 0) as the starting condition
sray.steer_rx(azimuth=0, elevation=0)
 
# Select PLL and gain-mode via the xud_control interface
ctx = conv._ctrl.ctx
xud = ctx.find_device("xud_control")
PLLselect = xud.find_channel("voltage1", True)
rxgainmode = xud.find_channel("voltage0", True)
PLLselect.attrs["raw"].value = "1"
rxgainmode.attrs["raw"].value = "1"
 
print("Hardware initialization complete.\n")
 
# ==========================================================================
# STEP 2 — Calibration  (gain + phase)
# ==========================================================================
# Calibration equalizes gain and phase across all 64 elements so the beam
# forms correctly.  This only needs to run once per power cycle (or if
# temperature changes significantly).
 
input("Place your horn antenna at boresight and make sure the RF source is ON.\n"
      "Press Enter to begin calibration...")
 
mr.enable_stingray_channel(sray, subarray)
 
# -- Gain calibration --
# Measures each element's gain and computes per-element VGA codes to
# equalize the array response.
print("\n[CAL] Running gain calibration...")
mr.disable_stingray_channel(sray)
gain_dict, atten_dict, mag_pre_cal, mag_post_cal = mr.rx_gain(sray, conv, subarray, adc_map, sray.element_map)
print("[CAL] Gain calibration complete.")
 
# -- Phase calibration --
# Finds the phase offset of each element relative to the reference element
# and programs compensating phase shifts into the ADAR1000s.
print("[CAL] Running phase calibration...")
cal_ant = mr.find_phase_delay_fixed_ref(sray, conv, subarray_ref, adc_ref, delay_phases)
analog_phase, analog_phase_dict = mr.phase_analog(sray, conv, adc_map, adc_ref, subarray_ref, subarray_targ, cal_ant)
print("[CAL] Phase calibration complete.\n")
 
# ==========================================================================
# STEP 3 — Helper: capture combined magnitude at a given steering angle
# ==========================================================================
def capture_at_angle(az, el=0):
    """Steer the beam to (az, el) degrees and return combined power of all 4 ADC channels.
 
    Returns:
        combined_mag (float): combined magnitude across all 4 channels (dBm)
    """
    sray.steer_rx(azimuth=az, elevation=el)
    sray.latch_rx_settings()
 
    mr.enable_stingray_channel(sray)
    steer_data = np.transpose(np.array(mr.data_capture(conv)))
    mr.disable_stingray_channel(sray)
 
    steer_data = np.array(steer_data).T
    steer_data = mr.cal_data(steer_data, cal_ant)
    steer_data = np.array(steer_data).T
 
    combined_data = np.sum(steer_data, axis=1)
    combined_mag = mr.get_analog_mag(combined_data, conv)
 
    return combined_mag
 
# ==========================================================================
# STEP 4 — Steering Demo: boresight vs. steered
# ==========================================================================
input("Calibration done. Press Enter to start the steering demo...")
 
print(f"\n--- Capturing at boresight (0 deg) ---")
mag_bore = capture_at_angle(az=0, el=0)
print(f"    Combined 4-channel magnitude: {mag_bore:.2f} dBm")
 
print(f"\n--- Steering beam to {STEER_ANGLE} deg azimuth ---")
mag_steered = capture_at_angle(az=STEER_ANGLE, el=0)
print(f"    Combined 4-channel magnitude: {mag_steered:.2f} dBm")
 
delta = mag_bore - mag_steered
print(f"\n{'='*50}")
print(f"  Boresight (0 deg):       {mag_bore:.2f} dBm")
print(f"  Steered ({STEER_ANGLE} deg):        {mag_steered:.2f} dBm")
print(f"  Signal drop:             {delta:.2f} dB")
print(f"{'='*50}")
if delta > 3:
    print(f"  PASS — Beam steering is working. Signal dropped {delta:.1f} dB")
    print(f"         when steering {STEER_ANGLE} deg away from the source.")
else:
    print(f"  WARNING — Expected a larger drop. Check horn placement")
    print(f"            and ensure the source is at true boresight.")
 
print("\nSteering demo complete.")
 