# ==========================================================================
# ADSY2301 — RX Array Calibration with External Spectrum Analyzer
# --------------------------------------------------------------------------
# This script adapts ADSY2301_Rx_Cal.py so the receive-path calibration uses
# an external Keysight N9000A / CXA spectrum analyzer for the measurements
# instead of the ADRV9009-ZU11EG converter capture path.
#
# PREREQUISITES
#   1. Run ADSY2301_bootstrap_tiles.py (or the equivalent shell commands
#      on the SoM) to initialize the ADAR1000 tiles.
#   2. Connect a CW RF source at the operating frequency.
#   3. Connect the array output to the spectrum analyzer.
#   4. Update SPEC_AN_ADDRESS and OPERATING_FREQUENCY_HZ as needed.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import os
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import matplotlib.pyplot as plt
import paramiko
import pyvisa

import adi
from Drivers import N9000A_Driver as N9000A
import ADSY2301 as mr


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
SELF_BIASED_LNAs = True
ARRAY_MODE = "rx"
URL = "ip:10.75.161.150"
OPERATING_FREQUENCY_HZ = 4.51e9
SPEC_AN_ADDRESS = "TCPIP0::10.75.161.57::hislip0::INSTR"
WAIT_TIME_S = 0.5
PHASE_STEPS = np.arange(-180, 181, 5)  # Coarse sweep; use 1-degree steps for finer tuning


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------
def configure_spectrum_analyzer(spec_an, center_freq_hz, span_hz=10e6):
    """Apply a simple measurement setup to the external spectrum analyzer."""
    spec_an.reset()
    spec_an.set_to_spec_an_mode()
    spec_an.set_center_freq(center_freq_hz)
    spec_an.set_freq_span(span_hz)
    spec_an.set_resolution_bandwidth(100e-6)
    spec_an.set_continuous_peak_search(1, 1)
    spec_an.set_attenuation(0)
    spec_an.set_reference_level(-40)
    spec_an.set_initiate_continuous_sweep("ON")
    time.sleep(0.5)


def measure_marker_power(spec_an, center_freq_hz, wait_time_s=WAIT_TIME_S):
    """Trigger one marker-power measurement on the spectrum analyzer."""
    spec_an.set_center_freq(center_freq_hz)
    time.sleep(wait_time_s)
    return float(spec_an.get_marker_power(marker=1))


def enable_elements_and_measure(spec_an, sray, elements, center_freq_hz):
    """Enable the requested elements, measure the power, and return the result."""
    mr.disable_stingray_channel(sray)
    mr.enable_stingray_channel(sray, elements)
    sray.latch_rx_settings()
    return measure_marker_power(spec_an, center_freq_hz)


def set_element_phase(sray, element_id, phase_deg):
    """Set the RX phase for a single element and latch the settings."""
    for element in sray.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        if value == element_id:
            element.rx_phase = phase_deg
            break
    sray.latch_rx_settings()


def compute_gain_codes_from_power(power_db, reference_index=0):
    """Map measured received power to RX gain codes.

    The goal is to make all elements land near the same measured power.
    Stronger elements receive a lower gain code; weaker elements receive a
    higher gain code. The mapping is intentionally simple and easy to tune.
    """
    power_db = np.asarray(power_db, dtype=float)
    ref_power = power_db[reference_index]
    gain_codes = np.clip(np.round(127.0 * (10.0 ** ((ref_power - power_db) / 20.0))), 0, 127)
    return gain_codes.astype(int)


# --------------------------------------------------------------------------
# Step 0 — SSH Connection & Hardware Initialization
# --------------------------------------------------------------------------
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="10.75.161.150", port=22, username="root", password="analog")

print("Connecting to", URL, "...")

# --------------------------------------------------------------------------
# Step 1 — Initialize the ADAR1000 array
# --------------------------------------------------------------------------
sray = adi.adar1000_array(
    uri=URL,
    chip_ids=[
        "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", "adar1000_csb_1_2_1", "adar1000_csb_1_2_4",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_2",
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", "adar1000_csb_0_2_1", "adar1000_csb_0_2_4",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2",
    ],

    device_map=[[6, 1, 8, 3], [5, 2, 7, 4], [14, 9, 16, 11], [13, 10, 15, 12]],

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
        1:  [25, 26, 18, 17],  3:  [57, 58, 50, 49],
        2:  [20, 19, 27, 28],  4:  [52, 51, 59, 60],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [9, 10, 2, 1],     8:  [41, 42, 34, 33],
        9:  [29, 30, 22, 21],  11: [61, 62, 54, 53],
        10: [24, 23, 31, 32],  12: [56, 55, 63, 64],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [13, 14, 6, 5],    16: [45, 46, 38, 37],
    },
)

# --------------------------------------------------------------------------
# Step 2 — Initial RX settings
# --------------------------------------------------------------------------
print("Setting all elements to RX mode with max gain and zero phase offset")
for element in sray.elements.values():
    element.rx_attenuator = 0
    element.rx_gain = 127
    element.rx_phase = 0
sray.latch_rx_settings()

# Point the array at boresight
sray.steer_rx(azimuth=0, elevation=0)

# --------------------------------------------------------------------------
# Step 3 — Connect and configure the spectrum analyzer
# --------------------------------------------------------------------------
rm = pyvisa.ResourceManager()
SpecAn = N9000A.N9000A(rm, SPEC_AN_ADDRESS)
configure_spectrum_analyzer(SpecAn, OPERATING_FREQUENCY_HZ, span_hz=2.5e6)

input("Make sure the RF source and the analyzer are connected correctly. Press Enter to continue...")

# --------------------------------------------------------------------------
# Step 4 — Gain calibration using the spectrum analyzer
# --------------------------------------------------------------------------
# Measure the power of each element one at a time and use it to derive
# RX gain codes that equalize the array.
reference_elements = np.array([1, 33, 37, 5])
all_elements = np.arange(1, 65)

print("Starting gain calibration...")
power_before = []
for element_id in all_elements:
    power_db = enable_elements_and_measure(SpecAn, sray, [int(element_id)], OPERATING_FREQUENCY_HZ)
    power_before.append(power_db)
    print(f"Element {element_id}: {power_db:.3f} dBm")

power_before = np.asarray(power_before, dtype=float)

# Use the strongest element as the calibration reference for the first pass.
reference_index = int(np.argmax(power_before))
gain_codes = compute_gain_codes_from_power(power_before, reference_index=reference_index)

for element in sray.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    element.rx_attenuator = 0
    element.rx_gain = int(gain_codes[value - 1])
sray.latch_rx_settings()

print("Writing gain codes to the array")
print("Gain codes:", gain_codes)

# Re-measure after applying the gain codes
power_after = []
for element_id in all_elements:
    power_db = enable_elements_and_measure(SpecAn, sray, [int(element_id)], OPERATING_FREQUENCY_HZ)
    power_after.append(power_db)
    print(f"Element {element_id}: {power_db:.3f} dBm")

power_after = np.asarray(power_after, dtype=float)

# --------------------------------------------------------------------------
# Step 5 — Phase calibration using the spectrum analyzer
# --------------------------------------------------------------------------
# Sweep the RX phase of each element and pick the phase that maximizes the
# combined power of the selected element and a reference element.
print("Starting phase calibration...")
phase_cal_values = []

for element_id in all_elements:
    if element_id in reference_elements:
        phase_cal_values.append(0)
        continue

    best_phase = 0
    best_power = -np.inf

    # Reset the target element to zero phase before the sweep.
    set_element_phase(sray, int(element_id), 0)
    set_element_phase(sray, int(reference_elements[0]), 0)

    for phase_deg in PHASE_STEPS:
        set_element_phase(sray, int(element_id), int(phase_deg))
        power_db = enable_elements_and_measure(SpecAn, sray, [int(reference_elements[0]), int(element_id)], OPERATING_FREQUENCY_HZ)
        if power_db > best_power:
            best_power = power_db
            best_phase = int(phase_deg)

    phase_cal_values.append(best_phase)
    print(f"Element {element_id}: best RX phase = {best_phase} deg")

    # Apply the best phase to the target element.
    set_element_phase(sray, int(element_id), best_phase)

# --------------------------------------------------------------------------
# Step 6 — Plot the results
# --------------------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

x = np.arange(1, 65)
axes[0].plot(x, power_before, marker="o", label="Before gain calibration")
axes[0].set_ylabel("Measured power (dBm)")
axes[0].set_title("RX calibration using spectrum analyzer")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(x, power_after, marker="o", color="tab:red", label="After gain calibration")
axes[1].set_xlabel("Element")
axes[1].set_ylabel("Measured power (dBm)")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig("ADSY2301_Rx_Cal_SpecAn.png")
print("Saved plot to ADSY2301_Rx_Cal_SpecAn.png")
plt.show()

print("Calibration complete. Review the plot and adjust the analyzer settings if needed.")
input("Press Enter to exit...")
