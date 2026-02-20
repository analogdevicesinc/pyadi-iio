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
import genalyzer as gn
# Import from Drivers folder (subfolder relative to this file)
from Drivers import N9000A_Driver as N9000A
from Drivers import E8267D_Driver as E8267D
from Drivers import N6705B_Driver as N6705B
from Drivers import E36233A_Driver as E36233A
# Import from Millibox folder (subfolder relative to this file)
from Millibox import mbx_functions as mbx



# ----------------------------
# USER SETTINGS
# ----------------------------
DEVICENAME = "/dev/ttyUSB0"
BAUDRATE = 57600

talise_ip = "192.168.1.1"
talise_uri = "ip:" + talise_ip

sig_gen_freq_GHz = 10
steering_angles = [0]          # broadside only
maxsweepangle = 120            # degrees (sweep -60..+60)
sweepstep = 1                  # degrees per step
settle_s = 0.35                # settle before reading marker power

# Output location
out_dir = "/home/snuc/Desktop/tx_beamforming_outputs"
os.makedirs(out_dir, exist_ok=True)


# ----------------------------
# VISA / INSTRUMENT SETUP
# ----------------------------
rm = pyvisa.ResourceManager()

E36 = "TCPIP::192.168.1.35::inst0::INSTR"
PA_Supplies = E36233A.E36233A(rm, E36)
PA_Supplies.output_off(1)
PA_Supplies.set_voltage(1, 18)
PA_Supplies.set_current(1, 30)

N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)
Pwr_Supplies.output_off(3)

CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
SpecAn = N9000A.N9000A(rm, CXA)


# ----------------------------
# GIMBAL SETUP
# ----------------------------
mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()
GIMBAL_H = mbx.H
GIMBAL_V = mbx.V


# ----------------------------
# ADAR1000 ARRAY SETUP
# ----------------------------
dev = adi.adar1000_array(
    uri=talise_uri,
    chip_ids=[
        "adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
        "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"
    ],
    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
    element_map=np.array([
        [1, 9,  17, 25, 33, 41, 49, 57],
        [2, 10, 18, 26, 34, 42, 50, 58],
        [3, 11, 19, 27, 35, 43, 51, 59],
        [4, 12, 20, 28, 36, 44, 52, 60],
        [5, 13, 21, 29, 37, 45, 53, 61],
        [6, 14, 22, 30, 38, 46, 54, 62],
        [7, 15, 23, 31, 39, 47, 55, 63],
        [8, 16, 24, 32, 40, 48, 56, 64]
    ]),
    device_element_map={
        1:  [9, 10, 2, 1],      3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],   4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],     7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],   8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],   12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],     15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],   16: [56, 55, 63, 64],
    }
)

# Configure T/R control as you’ve been using for TX
for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"
dev.latch_tx_settings()
dev.latch_rx_settings()
print("Initialized BFC Tile (TX config).")


# ----------------------------
# ARRAY / SUBARRAY DEFINITIONS
# ----------------------------
array_shapes = [
    [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46],
    [19,27,20,28,21,29,22,30,35,43,36,44,37,45,38,46,10,18,26,34,42,50,51,52,53,54,55,47,39,31,23,15,14,13,12,11],
    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64],  # 8x8
    [1,2,3,4,5,6,7,8,9,17,25,33,41,49,57,58,59,60,61,62,63,64,56,48,40,32,24,16],  # outer
    [33,34,35,36,41,42,43,44,49,50,51,52,57,58,59,60],  # subarray 2
    [37,38,39,40,45,46,47,48,53,54,55,56,61,62,63,64],  # subarray 3
    [5,6,7,8,13,14,15,16,21,22,23,24,29,30,31,32],       # subarray 4
    [1,2,3,4,9,10,11,12,17,18,19,20,25,26,27,28],        # subarray 1
]

desired_array_shape = "8x8"
if desired_array_shape != "8x8":
    raise ValueError("This script is set up for 8x8. Adjust active_array selection if needed.")

active_array = np.array(array_shapes[2])

# Δ flip sets (initial guess; the script will auto-fix Σ/Δ assignment regardless)
TX_DELTA_AZ_ELEMENTS = set(array_shapes[4] + array_shapes[5])  # SA2 + SA3
TX_DELTA_EL_ELEMENTS = set(array_shapes[5] + array_shapes[6])  # SA3 + SA4


# Capture calibrated phases already loaded in the array (post-calibration)
phase_dict_ref = active_array.transpose().flatten()
phase_dict = mr.create_dict(phase_dict_ref, np.zeros(64))
for element in dev.elements.values():
    idx = int(mr.strip_to_last_two_digits(str(element)))
    phase_dict[idx] = element.tx_phase


# ----------------------------
# SWEEP AXIS SETUP
# ----------------------------
gimbal_positions = np.arange(0, (maxsweepangle + 1), sweepstep)
angles = np.linspace(-(maxsweepangle/2), (maxsweepangle/2), len(gimbal_positions))
center_i = len(gimbal_positions) // 2  # ~boresight index


# ----------------------------
# HELPERS
# ----------------------------
def set_tx_phases(delta_elements=None):
    """Apply calibrated phases; if delta_elements provided, +180° on those elements."""
    for element in dev.elements.values():
        idx = int(mr.strip_to_last_two_digits(str(element)))
        ph = phase_dict[idx]
        if delta_elements is not None and idx in delta_elements:
            ph = (ph + 180) % 360
        element.tx_phase = ph
    dev.latch_tx_settings()


def reset_gimbal_to_start(gimbal_motor):
    """Move gimbal to -maxsweepangle/2 using gotoZERO + relative move."""
    mbx.gotoZERO()
    mbx.move(gimbal_motor, -(maxsweepangle/2))
    time.sleep(1.0)


def run_sweep(axis_name, gimbal_motor, steer_fn, delta_elements):
    """
    Measures two candidates at each angle:
      A = 'sum_candidate'  (no flip)
      B = 'delta_candidate' (with flip)
    Then auto-assigns:
      Σ = whichever is higher at boresight (center angle)
      Δ = the other
    Returns:
      sum_dict, delta_dict keyed by steering angle
    """
    sum_candidate = {sa: np.zeros(len(gimbal_positions)) for sa in steering_angles}
    delta_candidate = {sa: np.zeros(len(gimbal_positions)) for sa in steering_angles}

    reset_gimbal_to_start(gimbal_motor)

    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 7))
    try:
        fig.canvas.manager.window.showMaximized()
    except:
        pass

    for i in range(len(gimbal_positions)):
        for sa in steering_angles:
            az, el = steer_fn(sa)

            dev.steer_tx(azimuth=az, elevation=el)
            dev.latch_tx_settings()

            # Candidate A (no flip)
            set_tx_phases(delta_elements=None)
            time.sleep(settle_s)
            sum_candidate[sa][i] = SpecAn.get_marker_power(marker=1)

            # Candidate B (with flip)
            set_tx_phases(delta_elements=delta_elements)
            time.sleep(settle_s)
            delta_candidate[sa][i] = SpecAn.get_marker_power(marker=1)

            # Restore calibrated phases
            set_tx_phases(delta_elements=None)

        # Live plot: show candidates (auto-assignment will happen after sweep)
        sa0 = steering_angles[0]
        x = angles[:i+1]
        ax.clear()
        ax.plot(x, sum_candidate[sa0][:i+1], color="blue", linewidth=2, marker="o", markersize=4, label="Candidate A (no flip)")
        ax.plot(x, delta_candidate[sa0][:i+1], color="orange", linewidth=2, marker="o", markersize=4, label="Candidate B (flip)")
        ax.set_title(f"TX {axis_name} (live candidates) @ {sig_gen_freq_GHz} GHz")
        ax.set_xlabel(f"Mechanical {axis_name} Angle (deg)")
        ax.set_ylabel("TX Power (dBm)")
        ax.set_xlim([-(maxsweepangle/2), (maxsweepangle/2)])
        all_data = np.concatenate([sum_candidate[sa0][:i+1], delta_candidate[sa0][:i+1]])
        ax.set_ylim(np.nanmin(all_data) - 10, np.nanmax(all_data) + 10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)

        mbx.move(gimbal_motor, sweepstep)

    plt.ioff()

    # Auto-assign Σ/Δ based on which is higher at boresight
    sum_dict = {sa: np.copy(sum_candidate[sa]) for sa in steering_angles}
    delta_dict = {sa: np.copy(delta_candidate[sa]) for sa in steering_angles}

    sa0 = steering_angles[0]
    a0 = sum_candidate[sa0][center_i]
    b0 = delta_candidate[sa0][center_i]

    # Σ must be the larger at boresight
    if b0 > a0:
        # swap
        for sa in steering_angles:
            sum_dict[sa], delta_dict[sa] = delta_dict[sa], sum_dict[sa]
        print(f"[{axis_name}] Auto-swap applied: Σ=flip-candidate (boresight {b0:.2f} dBm) > noflip-candidate ({a0:.2f} dBm)")
    else:
        print(f"[{axis_name}] No swap: Σ=noflip-candidate (boresight {a0:.2f} dBm) >= flip-candidate ({b0:.2f} dBm)")

    return sum_dict, delta_dict


# ----------------------------
# MAIN
# ----------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

PA_Supplies.output_on(1)
mr.enable_pa_bias_channel(dev, active_array)
time.sleep(2)

print("Starting TX Azimuth sweep (auto-correct Σ/Δ)...")
az_sum, az_delta = run_sweep(
    axis_name="Azimuth",
    gimbal_motor=GIMBAL_H,
    steer_fn=lambda sa: (sa, 0),
    delta_elements=TX_DELTA_AZ_ELEMENTS
)

print("Starting TX Elevation sweep (auto-correct Σ/Δ)...")
el_sum, el_delta = run_sweep(
    axis_name="Elevation",
    gimbal_motor=GIMBAL_V,
    steer_fn=lambda sa: (0, sa),
    delta_elements=TX_DELTA_EL_ELEMENTS
)

mr.disable_pa_bias_channel(dev, active_array)
mbx.gotoZERO()
set_tx_phases(delta_elements=None)

# ----------------------------
# SAVE PNG OVERLAYS (Σ blue, Δ orange) — guaranteed by auto-correct
# ----------------------------
sa0 = steering_angles[0]

az_png = os.path.join(out_dir, f"tx_az_sum_delta_{sig_gen_freq_GHz}GHz_{timestamp}.png")
plt.figure(figsize=(12, 7))
plt.plot(angles, az_sum[sa0], color="blue", linewidth=2, label="Σ (Sum)")
plt.plot(angles, az_delta[sa0], color="orange", linewidth=2, label="Δ (Delta)")
plt.title(f"TX Azimuth Monopulse (Σ/Δ) @ {sig_gen_freq_GHz} GHz (SA={sa0}°)")
plt.xlabel("Mechanical Azimuth Angle (deg)")
plt.ylabel("TX Power (dBm)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(az_png, dpi=200)
plt.close()

el_png = os.path.join(out_dir, f"tx_el_sum_delta_{sig_gen_freq_GHz}GHz_{timestamp}.png")
plt.figure(figsize=(12, 7))
plt.plot(angles, el_sum[sa0], color="blue", linewidth=2, label="Σ (Sum)")
plt.plot(angles, el_delta[sa0], color="orange", linewidth=2, label="Δ (Delta)")
plt.title(f"TX Elevation Monopulse (Σ/Δ) @ {sig_gen_freq_GHz} GHz (SA={sa0}°)")
plt.xlabel("Mechanical Elevation Angle (deg)")
plt.ylabel("TX Power (dBm)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(el_png, dpi=200)
plt.close()

print("Saved PNG overlays:")
print(" ", az_png)
print(" ", el_png)

# ----------------------------
# SAVE MATLAB .MAT (POWER-DOMAIN)
# ----------------------------
mat_path = os.path.join(out_dir, f"tx_monopulse_az_el_{sig_gen_freq_GHz}GHz_{timestamp}.mat")

tx_mat = {
    "frequency_GHz": float(sig_gen_freq_GHz),
    "steering_angles_deg": np.array(steering_angles),
    "mechanical_angles_deg": np.array(angles),

    # Σ/Δ power patterns (boresight-corrected)
    "tx_az_sum_dBm": np.array(az_sum[sa0]),
    "tx_az_delta_dBm": np.array(az_delta[sa0]),
    "tx_el_sum_dBm": np.array(el_sum[sa0]),
    "tx_el_delta_dBm": np.array(el_delta[sa0]),

    # What you flipped (candidate definition; final Σ/Δ handled by auto-correct)
    "delta_az_elements_initial": np.array(sorted(list(TX_DELTA_AZ_ELEMENTS))),
    "delta_el_elements_initial": np.array(sorted(list(TX_DELTA_EL_ELEMENTS))),

    "active_array": np.array(active_array),
    "description": (
        "Manta Ray TX azimuth + elevation sweeps with Σ/Δ monopulse. "
        "Measured via spectrum analyzer marker power. Σ/Δ assignment auto-corrected so Σ peaks at boresight."
    )
}

savemat(mat_path, tx_mat, do_compression=True)
print("Saved MAT:", mat_path)

print("Done.")