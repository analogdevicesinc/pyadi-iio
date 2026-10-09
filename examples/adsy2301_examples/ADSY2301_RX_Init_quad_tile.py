# ==========================================================================
# ADSY2301 — Quad Tile RX Initialization (64 Elements)
# --------------------------------------------------------------------------
# Initializes the full 64-element array (16 x ADAR1000) for RX operation:
#   - ADAR1000 beamformers, Up/Down Converter (UDC) and ADRV9009 transceiver
#   - SDR and TDD engine configuration (RX)
#   - UDC RX Band 3 (RF 10-11 GHz, LO 14.9 GHz)
#   - All elements set to max RX gain, no attenuation and 0 degree phase
#
# RX channels are left disabled. Uncomment the lines at the end of the
# script to enable all or selected channels.
#
# This script is intended for interactive use — run it, then inspect or
# modify `dev` and `mr` in your debugger console.
#
# No external instruments are required.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
from adi import adsy2301 as mr
import numpy as np

##############################################
## Step 1: Connect to ADSY2301 ##
##############################################
# talise_ip = "10.75.161.115"
talise_ip = "10.75.161.151"
talise_uri = "ip:" + talise_ip

print("Initializing ADSY2301 with IP address: " + talise_uri)
dev = mr.adsy2301(uri=talise_uri)

##############################################
## Step 2: Initialize ADAR1000 Array (16 x ADAR1000) ##
##############################################
dev.init_BFC(

    chip_ids=[
        "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", "adar1000_csb_1_2_1", "adar1000_csb_1_2_4",
        "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_2",
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", "adar1000_csb_0_2_1", "adar1000_csb_0_2_4",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2",
    ],

    device_map=[[6, 1, 8, 3], [5, 2, 7, 4], [14, 9, 16, 11], [13, 10, 15, 12]],

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

##############################################
## Step 3: Initialize UDC and ADRV9009 ##
##############################################
# Up/Down Converter: ADF4382 LO, ADMV1320, ADMV1420, ADMV8913, ADRF5030
dev.init_UDC()

# ADRV9009 transceiver, SDR and TDD engine (TXRX_Bit=0 -> RX)
dev.init_ADRV9009()
mr.sdr_init(dev)
mr.tdd_init(dev, TXRX_Bit=0)

# Put all beamformers into a known default state
dev.BFC.initialize_devices(pa_off=-4.8, pa_on=-4.8, lna_off=-4.8, lna_on=-4.8)

##############################################
## Step 4: UDC RX Band Selection ##
##############################################
# Band 3: RF 10-11 GHz, LO 14.9 GHz. Includes the ADRF5030 RX switch,
# ADMV8913 filter and ADF4382 LO settings, so the individual calls below
# are not needed.
# dev.udc.adrf5030.RX_SW_Enable()
# dev.udc.admv8913.set_filter_widest()
# dev.udc.adf4382.altvolt0_frequency = int(14.89e9)
# dev.udc.adf4382.altvolt1_frequency = int(14.89e9)
dev.udc.RX_UDC_Band_3()

##############################################
## Step 5: Configure RX Mode ##
##############################################
for device in dev.BFC.devices.values():
    device.mode = "rx"
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

print("Setting all elements to default RX settings")
for element in dev.BFC.elements.values():
    element.rx_attenuator = 0  # 1: Attenuation on; 0: Attenuation off
    element.tx_attenuator = 0
    element.rx_gain = 127      # 127: Highest gain; 0: Lowest gain
    element.tx_gain = 0        # Lowest gain
    element.rx_phase = 0       # Set all phases to 0
    element.tx_phase = 0

dev.BFC.latch_rx_settings()
dev.BFC.latch_tx_settings()

##############################################
## OPTIONAL: Enable/Disable RX Channels ##
##############################################
# Uncomment to enable all RX channels
# mr.enable_rx_channel(dev.BFC)

# Uncomment to enable specific RX channels
# mr.enable_rx_channel(dev.BFC, [1, 2, 3])

# Uncomment to disable all RX channels
# mr.disable_rx_channel(dev.BFC)