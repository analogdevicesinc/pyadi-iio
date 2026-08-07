# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""JESD SerDes PRBS test for Washington (apollo_som_vu11p / ADSY1100).

Both ends of each JESD lane must be in PRBS mode simultaneously:
  - FPGA GTY TX sends PRBS -> Apollo JRx checker (bist_prbs_select_jrx)
  - Apollo JTx sends PRBS  -> FPGA GTY RX checker (rx_a/rx_b prbs_select)

The external loopbacks connect FPGA TX to Apollo JRx and Apollo JTx to FPGA RX.
Because the Apollo PCS re-encodes data, raw PRBS only survives if both ends agree.
"""

import time

import adi

IP = "ip:10.48.65.110"
PRBS = adi.adxcvr.PRBS_7

# --- FPGA GTY adxcvr instances (axi_adxcvr driver via sysfs) ---------------
# A-side: GTY quads 128-130, 12 lanes; B-side: GTY quads 125-127, 12 lanes
rx_a = adi.adxcvr(IP, "axi-adxcvr-rx")
tx_a = adi.adxcvr(IP, "axi-adxcvr-tx")
rx_b = adi.adxcvr(IP, "axi-adxcvr-rx-b")
tx_b = adi.adxcvr(IP, "axi-adxcvr-tx-b")

# --- Apollo digitizer SerDes (ad9088 IIO debugfs) ---------------------------
# Single control point: axi-ad9084-rx-hpc drives both A and B side Apollo lanes
apollo = adi.apollo_serdes(IP)

# --- Enable PRBS on both ends simultaneously ---------------------------------
# FPGA TX generators
tx_a.prbs_select = PRBS
tx_b.prbs_select = PRBS

# Apollo JTx generator -> FPGA RX checker
apollo.prbs_select_jtx = PRBS

# FPGA RX checkers
rx_a.prbs_select = PRBS
rx_b.prbs_select = PRBS

# Apollo JRx checker <- FPGA TX
apollo.prbs_select_jrx = PRBS

# Give lanes time to lock, then clear counters before measuring
time.sleep(1)
rx_a.reset_prbs_counters()
rx_b.reset_prbs_counters()

time.sleep(2)

# --- Read results ------------------------------------------------------------
print("=== FPGA GTY RX (PRBS from Apollo JTx) ===")
print("A-side status :", rx_a.prbs_status)
print("A-side errors :", rx_a.prbs_error_counters)
print("B-side status :", rx_b.prbs_status)
print("B-side errors :", rx_b.prbs_error_counters)

print()
print("=== Apollo JRx (PRBS from FPGA GTY TX) ===")
for entry in apollo.prbs_error_counters_jrx:
    status = "OK" if entry["err_count"] == 0 else "ERRORS"
    print(f"  {entry['side']}-side lane {entry['lane']:2d}: {entry['err_count']} errors  [{status}]")

# --- Restore normal JESD data path ------------------------------------------
apollo.prbs_select_jrx = adi.apollo_serdes.PRBS_OFF
apollo.prbs_select_jtx = adi.apollo_serdes.PRBS_OFF
rx_a.prbs_select = adi.adxcvr.PRBS_OFF
rx_b.prbs_select = adi.adxcvr.PRBS_OFF
tx_a.prbs_select = adi.adxcvr.PRBS_OFF
tx_b.prbs_select = adi.adxcvr.PRBS_OFF
