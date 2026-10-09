# ==========================================================================
# ADSY2301 — Quad Tile TX Initialization (64 Elements)
# --------------------------------------------------------------------------
# Initializes the full 64-element array (16 x ADAR1000) for TX operation:
#   - Beamformer PA and power rails held off during setup
#   - ADAR1000 beamformers, Up/Down Converter (UDC) and ADRV9009 transceiver
#   - SDR and TDD engine configuration
#   - All elements set to max TX gain, no attenuation and 0 degree phase
#   - TR source switched to FPGA (external) with PA bias toggle
#   - UDC TX Band 0, then PA and power rails enabled
#   - TX channel on element 33 enabled
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
# host_ip = "10.75.161.115"
host_ip = "10.75.161.151"
host_uri = "ip:" + host_ip

print("Initializing ADSY2301 with IP address: " + host_uri)
dev = mr.adsy2301(uri=host_uri)

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

# Hold beamformer PA and power rails off during setup
dev.BFC.BF_PA_ON_01 = 0
dev.BFC.BF_PA_ON_02 = 0
dev.BFC.BF_PA_ON_03 = 0
dev.BFC.BF_PA_ON_04 = 0

dev.BFC.BF_PWR_EN_01 = 0
dev.BFC.BF_PWR_EN_02 = 0
dev.BFC.BF_PWR_EN_03 = 0
dev.BFC.BF_PWR_EN_04 = 0

##############################################
## Step 3: Initialize UDC and ADRV9009 ##
##############################################
# Up/Down Converter: ADF4382 LO, ADMV1320, ADMV1420, ADMV8913, ADRF5030
dev.init_UDC()

# ADRV9009 transceiver
dev.init_ADRV9009()

# Put all beamformers into a known default state
dev.BFC.initialize_devices(pa_off=-4.8, pa_on=-4.8, lna_off=-4.8, lna_on=-4.8)

# UDC defaults: TX switch, widest filter, LO at 14.9 GHz
dev.udc.adrf5030.TX_SW_Enable()
dev.udc.admv8913.set_filter_widest()
dev.udc.adf4382.altvolt0_frequency = int(14.9e9)
dev.udc.adf4382.altvolt1_frequency = int(14.9e9)

# SDR and TDD engine configuration
mr.sdr_init(dev)
mr.tdd_init(dev, TXRX_Bit=0)

##############################################
## Step 4: Configure Beamformer Defaults ##
##############################################
for device in dev.BFC.devices.values():
    device.tr_source = "spi"
    device.bias_dac_mode = "on"
    device.mode = "rx"

mr.disable_rx_channel(dev.BFC)
mr.disable_tx_channel(dev.BFC)

print("Setting all elements to default TX settings")
for element in dev.BFC.elements.values():
    element.rx_attenuator = 0  # 1: Attenuation on; 0: Attenuation off
    element.tx_attenuator = 0
    element.rx_gain = 0        # Lowest gain
    element.tx_gain = 127      # 127: Highest gain; 0: Lowest gain
    element.rx_phase = 0       # Set all phases to 0
    element.tx_phase = 0

dev.BFC.latch_rx_settings()
dev.BFC.latch_tx_settings()

##############################################
## Step 5: Enable TX ##
##############################################
# Switch TR source to FPGA-controlled (external) and enable bias toggle
# so the TDD engine gates the PA on/off each pulse.
for device in dev.BFC.devices.values():
    device.bias_dac_mode = "toggle"
    device.tr_source = "external"

# UDC TX band configuration
dev.udc.TX_UDC_Band_0()

# Enable beamformer PA and power rails
dev.BFC.BF_PA_ON_01 = 1
dev.BFC.BF_PA_ON_02 = 1
dev.BFC.BF_PA_ON_03 = 1
dev.BFC.BF_PA_ON_04 = 1

dev.BFC.BF_PWR_EN_01 = 1
dev.BFC.BF_PWR_EN_02 = 1
dev.BFC.BF_PWR_EN_03 = 1
dev.BFC.BF_PWR_EN_04 = 1

# Enable TX on element 33
mr.enable_tx_channel(dev.BFC, 33)

