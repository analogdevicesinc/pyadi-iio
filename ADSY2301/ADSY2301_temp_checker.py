# ADAR1000 Temperature Monitor
# Polls all 16 ADAR1000 temperature sensors every 5 seconds
# Per ADAR1000 datasheet: Temp (°C) ≈ raw_code * 1.0 - 78
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
 
import time
import adi
import numpy as np
from datetime import datetime
 
###############################################
## Configuration                             ##
###############################################
talise_ip = "192.168.1.1"
talise_uri = "ip:" + talise_ip
POLL_INTERVAL_S = 5   # seconds between polls
 
###############################################
## Initialize array                          ##
###############################################
dev = adi.adar1000_array(
    uri=talise_uri,
    chip_ids=[
        "adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
        "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4",
    ],
    device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
    element_map=np.array([
        [1,  9,  17, 25, 33, 41, 49, 57],
        [2,  10, 18, 26, 34, 42, 50, 58],
        [3,  11, 19, 27, 35, 43, 51, 59],
        [4,  12, 20, 28, 36, 44, 52, 60],
        [5,  13, 21, 29, 37, 45, 53, 61],
        [6,  14, 22, 30, 38, 46, 54, 62],
        [7,  15, 23, 31, 39, 47, 55, 63],
        [8,  16, 24, 32, 40, 48, 56, 64],
    ]),
    device_element_map={
        1:  [9, 10, 2, 1],     3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],  4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],  8:  [52, 51, 59, 60],
        9:  [13, 14, 6, 5],    11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],  12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],  16: [56, 55, 63, 64],
    },
)
 
def raw_to_celsius(raw_code):
    """Convert ADAR1000 temp sensor raw ADC code to °C.
    Calibrated: raw ~160 ≈ 30°C ambient, so offset = 130."""
    return raw_code - 130
 
###############################################
## Poll loop                                 ##
###############################################
# Build short labels from device_map ordering
dev_labels = {}
for idx, (chip_id, device) in enumerate(dev.devices.items()):
    dev_labels[chip_id] = f"Dev{chip_id:2d}"
 
# Print header
header_parts = [f"{'Timestamp':<20}"]
for chip_id in dev.devices:
    header_parts.append(f"{dev_labels[chip_id]:>10}")
header_parts.append(f"{'Avg':>8}")
header_parts.append(f"{'Min':>8}")
header_parts.append(f"{'Max':>8}")
header = " | ".join(header_parts)
 
print("ADAR1000 Temperature Monitor")
print(f"Polling every {POLL_INTERVAL_S} seconds. Press Ctrl+C to stop.")
print(f"Conversion: T(°C) = raw - 130\n")
print(header)
print("-" * len(header))
 
try:
    while True:
        temps = dev.temperatures
        temp_c = {chip_id: raw_to_celsius(raw) for chip_id, raw in temps.items()}
        values = list(temp_c.values())
 
        row_parts = [f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<20}"]
        for chip_id in dev.devices:
            row_parts.append(f"{temp_c[chip_id]:>7.0f} °C")
        row_parts.append(f"{np.mean(values):>5.1f} °C")
        row_parts.append(f"{np.min(values):>5.0f} °C")
        row_parts.append(f"{np.max(values):>5.0f} °C")
        print(" | ".join(row_parts))
 
        time.sleep(POLL_INTERVAL_S)
 
except KeyboardInterrupt:
    print("\nMonitoring stopped.")