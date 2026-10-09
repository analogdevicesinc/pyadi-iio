# ==========================================================================
# ADSY2301 — Single Tile RX Initialization (Beamformers Only)
# --------------------------------------------------------------------------
# Initializes a single 16-element tile (4 x ADAR1000) into RX mode with
# maximum RX gain, no attenuation and 0 degree phase on every element.
#
# By default only the ADAR1000 beamformers are configured. The Up/Down
# Converter (ADF4382 LO, ADMV1320/ADMV1420, ADMV8913, ADRF5030) and the
# ADRV9009 transceiver/TDD sections are left commented out. Uncomment the
# marked OPTIONAL blocks to enable them.
#
# This script is intended for interactive use — run it, then inspect or
# modify `dev` and `mr` in your debugger console.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
from adi import adsy2301 as mr
import numpy as np

##############################################
## Step 1: Connect to ADSY2301 ##
##############################################
host_ip = "10.75.161.151"
host_uri = "ip:" + host_ip

print("Initializing ADSY2301 with IP address: " + host_uri)
dev = mr.adsy2301(uri=host_uri)

##############################################
## Step 2: Initialize ADAR1000 Single Tile ##
##############################################
dev.init_BFC(
    chip_ids=[
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4",
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2",
    ],
    device_map=[[1, 3, 2, 4]],
    element_map=np.array([
        [1, 5,  9, 13],
        [2, 6, 10, 14],
        [3, 7, 11, 15],
        [4, 8, 12, 16],
    ]),
    device_element_map={
        1: [5, 6, 2, 1],  3: [13, 14, 10, 9],
        2: [4, 3, 7, 8],  4: [12, 11, 15, 16],
    },
)

##############################################
## OPTIONAL: Up/Down Converter (UDC) ##
##############################################
# Uncomment to create the UDC subclass (ADF4382 LO, ADMV1320, ADMV1420,
# ADMV8913 filter bank, ADRF5030 switch). Required for the band setup below.
# dev.init_UDC()

##############################################
## OPTIONAL: ADRV9009 Transceiver + TDD ##
##############################################
# Uncomment to create the ADRV9009 subclass and configure the SDR and
# TDD engine (TXRX_Bit=0 -> RX).
# dev.init_ADRV9009()
# mr.sdr_init(dev)
# mr.tdd_init(dev, TXRX_Bit=0)

##############################################
## Step 3: Beamformer Default State ##
##############################################
dev.BFC.initialize_devices(pa_off=-4.8, pa_on=-4.8, lna_off=-4.8, lna_on=-4.8)

##############################################
## OPTIONAL: UDC RX Band Selection ##
##############################################
# Requires dev.init_UDC() above. Band 3: RF 10-11 GHz, LO 14.9 GHz.
# Includes the ADRF5030 RX switch, ADMV8913 filter and ADF4382 LO settings.
# dev.udc.RX_UDC_Band_3()

##############################################
## Step 4: Configure RX Mode ##
##############################################
for device in dev.BFC.devices.values():
    device.mode = "rx"
    device.tr_source = "spi"
    device.bias_dac_mode = "on"

mr.disable_rx_channel(dev.BFC)
mr.disable_tx_channel(dev.BFC)

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
## OPTIONAL: Enable RX Channels ##
##############################################
# Uncomment to enable all RX channels
# mr.enable_rx_channel(dev.BFC)

# Uncomment to enable specific RX channels
# mr.enable_rx_channel(dev.BFC, [1, 2, 3])
