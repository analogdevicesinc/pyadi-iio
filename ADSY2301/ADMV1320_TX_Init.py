# ==========================================================================
"""ADMV1320 Microwave Downconverter Example

Demonstrates configuration of the ADMV1320 receive downconverter using pyadi-iio.

The ADMV1320 converts RF signals to IF/baseband signals across four selectable
RF bands (0.1-2 GHz, 1-5 GHz, 3-13 GHz, 6-20 GHz). It includes digitally
selectable attenuators (DSAs), configurable LO sideband/filter, and on-chip
temperature and power sensors.

For standalone use, set the URI to the target device.
For Neponset board use, specify the device instance name (e.g., "admv1320_rx_0").
"""
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================
import adi
import numpy as np
import json
import os
import ADSY2301 as mr

##############################################
## Step 1: Initialize ADMV 1320 ##
##############################################
# talise_ip = "10.75.161.115"
# talise_ip = "10.75.161.140"
talise_ip = "10.75.161.150"
talise_uri = "ip:" + talise_ip

tx_0 = adi.admv1320(uri=talise_uri, device_name="admv1320_tx_0")
tx_1 = adi.admv1320(uri=talise_uri, device_name="admv1320_tx_1")
tx_2 = adi.admv1320(uri=talise_uri, device_name="admv1320_tx_2")
tx_3 = adi.admv1320(uri=talise_uri, device_name="admv1320_tx_3")

READCURRENTSTATE = True
WRITENEWSTATE = False
WRITELUTTABLES = False

if READCURRENTSTATE:
    for tx in [tx_0, tx_1, tx_2, tx_3]:
        # --- Read current configuration ---
        print("=== ADMV1320 Current Configuration ===")
        print(f"Device Name:              {tx._device_name}")
        print(f"RF Band:                  {tx.rf_band}")
        print(f"RF Band Avail:            {tx.rf_band_available}")
        print(f"RF DSA1 Gain:             {tx.rf_direct_dsa1_gain}")
        print(f"RF DSA1 Gain Avail:       {tx.rf_direct_dsa1_gain_available}")
        print(f"RF DSA2 Gain:             {tx.rf_direct_dsa2_gain}")
        print(f"RF DSA2 Gain Avail:       {tx.rf_direct_dsa2_gain_available}")
        print(f"RF LPF:                   {tx.rf_direct_lpf_val}")
        print(f"RF HPF:                   {tx.rf_direct_hpf_val}")
        print(f"RF DSA1 Offset:           {tx.rf_direct_dsa1_offset}")
        print(f"RF DSA2 Offset:           {tx.rf_direct_dsa2_offset}")
        print(f"RF Bypass LPF En:         {tx.rf_bypass_lpf_en}")
        print(f"RF Bypass LPF Val:        {tx.rf_bypass_lpf_val}")
        print(f"RF Bypass HPF En:         {tx.rf_bypass_hpf_en}")
        print(f"RF Bypass HPF Val:        {tx.rf_bypass_hpf_val}")
        print(f"RF Bypass DSA1 Gain:      {tx.rf_bypass_dsa1_gain}")
        print(f"RF Bypass DSA1 Avail:     {tx.rf_bypass_dsa1_gain_available}")
        print(f"RF Bypass DSA2 Gain:      {tx.rf_bypass_dsa2_gain}")
        print(f"RF Bypass DSA2 Avail:     {tx.rf_bypass_dsa2_gain_available}")

        print(f"\nIF Band:                  {tx.if_band}")
        print(f"IF Band Avail:            {tx.if_band_available}")
        print(f"IF Mode:                  {tx.if_mode}")
        print(f"IF Mode Avail:            {tx.if_mode_available}")
        print(f"IF VCM:                   {tx.if_vcm}")
        print(f"IF DSA I 0.1dB:           {tx.if_dsai_0p1db}")
        print(f"IF DSA I 0.1dB Avail:     {tx.if_dsai_0p1db_available}")
        print(f"IF DSA Q 0.1dB:           {tx.if_dsaq_0p1db}")
        print(f"IF DSA Q 0.1dB Avail:     {tx.if_dsaq_0p1db_available}")

        print(f"\nLO Sideband:              {tx.lo_sideband}")
        print(f"LO Sideband Avail:        {tx.lo_sideband_available}")
        print(f"LO x3 Filter:            {tx.lo_x3_filter}")
        print(f"LO x3 Filter Avail:      {tx.lo_x3_filter_available}")
        print(f"LO I Phase:               {tx.lo_direct_i_phase_val}")
        print(f"LO Q Phase:               {tx.lo_direct_q_phase_val}")
        print(f"LO LON Offset I:          {tx.lo_direct_lon_offset_i}")
        print(f"LO LON Offset Q:          {tx.lo_direct_lon_offset_q}")

        # --- Direct register access (scratchpad test) ---
        print("\n=== Register Access ===")
        tx.reg_write(0x00A, 0xA5)
        val = tx.reg_read(0x00A)
        print(f"Scratchpad:               0x{int(val, 0):02X} (expected 0xA5)")



if WRITENEWSTATE:
    for tx in [tx_0, tx_1, tx_2, tx_3]:
        # --- Configure for 3-10 GHz RF band with IF input ---
        print("\n=== Configuring for 3-10 GHz band ===")
        tx.rf_band = "3GHz_10GHz"
        tx.if_band = "3GHz_12GHz"
        tx.if_mode = "if"
        tx.lo_sideband = "USB"
        tx.lo_x3_filter = "11GHz_13GHz"

        # Set DSA gains to 0 dB
        tx.rf_direct_dsa1_gain = "0dB"
        tx.rf_direct_dsa2_gain = "0dB"

        # Set IF common mode voltage (64 * 50mV = 3.2V)
        tx.if_vcm = 64

        # Set LO phase
        tx.lo_direct_i_phase_val = 15
        tx.lo_direct_q_phase_val = 15

        # --- Read back ---
        print(f"RF Band:           {tx.rf_band}")
        print(f"IF Band:           {tx.if_band}")
        print(f"IF Mode:           {tx.if_mode}")
        print(f"IF VCM:            {tx.if_vcm}")
        print(f"LO Sideband:       {tx.lo_sideband}")
        print(f"LO x3 Filter:     {tx.lo_x3_filter}")

        # --- Device-level attributes ---
        print(f"\n=== LUT and GPO Configuration ===")
        print(f"Filter Table:             {tx.filter_table_en}")
        print(f"Filter Load:              {tx.filter_load_en}")
        print(f"Filter Sel:               {tx.filter_table_sel}")
        print(f"Gain Table:               {tx.gain_table_en}")
        print(f"Gain Load:                {tx.gain_load_en}")
        print(f"Bypass Gain En:           {tx.bypass_gain_table_en}")
        print(f"Mixer Bypass:             {tx.mixer_bypass_en}")
        print(f"GPO_F:                    {tx.direct_gpo_f}")
        print(f"GPO_F OE:                 {tx.gpo_f_oe}")
        print(f"GPO_G:                    {tx.direct_gpo_g}")
        print(f"GPO_G OE:                 {tx.gpo_g_oe}")
        print(f"Bypass GPO_G:             {tx.bypass_gpo_g}")

if WRITELUTTABLES:
    for tx in [tx_0, tx_1, tx_2, tx_3]:

        # --- Write and readback LUT table configurations ---

        #LUTA_X RF (band,lpf,hpf,dsa1_off,dsa2_off,gpo_f) IF (if_gain_i,if_gain_q) LO (filter,sideband,i,q,lon_off_i,lon_off_q)
        print("\n=== Writing Filter Table A ===")
        filter_lut_a = """\
        LUTA_0 RF (0_2GHz,5,3,0,0,0) IF (0dB,0dB) LO (8GHz_9GHz,LSB,15,15,0,0)
        LUTA_1 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_2 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_3 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_4 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_5 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_6 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_7 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_8 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_9 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_10 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_11 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_12 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_13 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_14 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_15 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_16 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_17 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_18 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_19 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_20 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_21 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_22 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_23 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_24 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_25 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_26 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_27 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_28 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_29 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_30 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTA_31 RF (6GHz_20GHz,0,0,0,0,0) IF (0dB,0dB) LO (23GHz_28GHz,USB,0,0,0,0)"""

        tx.filter_table_config_A = filter_lut_a
        print("Filter Table A written successfully")
        print(f"Filter Cfg A readback:\n{tx.filter_table_config_A}")

        #LUTB_X RF (band,lpf,hpf,dsa1_off,dsa2_off,gpo_f) IF (if_gain_i,if_gain_q) LO (filter,sideband,i,q,lon_off_i,lon_off_q)
        print("\n=== Writing Filter Table B ===")
        filter_lut_b = """\
        LUTB_0 RF (1GHz_5GHz,7,7,0,0,0) IF (-1500mdB,-1500mdB) LO (13GHz_17GHz,USB,31,31,0,0)
        LUTB_1 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_2 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_3 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_4 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_5 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_6 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_7 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_8 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_9 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_10 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_11 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_12 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_13 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_14 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_15 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_16 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_17 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_18 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_19 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_20 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_21 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_22 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_23 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_24 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_25 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_26 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_27 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_28 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_29 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_30 RF (6GHz_20GHz,0,15,0,0,0) IF (-800mdB,-800mdB) LO (8GHz_9GHz,LSB,0,0,0,0)
        LUTB_31 RF (3GHz_10GHz,1,1,0,0,0) IF (-500mdB,-500mdB) LO (17GHz_23GHz,LSB,5,5,0,0)"""

        tx.filter_table_config_B = filter_lut_b
        print("Filter Table B written successfully")
        print(f"Filter Cfg B readback:\n{tx.filter_table_config_B}")

        #GAIN_X RF (dsa1,dsa2) gpo_g
        print("\n=== Writing Gain Table ===")
        gain_lut = """\
        GAIN_0 RF (-5dB,0dB) 15
        GAIN_1 RF (-1dB,0dB) 0
        GAIN_2 RF (-2dB,0dB) 0
        GAIN_3 RF (-3dB,0dB) 0
        GAIN_4 RF (-4dB,0dB) 0
        GAIN_5 RF (-5dB,0dB) 0
        GAIN_6 RF (-6dB,0dB) 0
        GAIN_7 RF (-7dB,0dB) 0
        GAIN_8 RF (-8dB,0dB) 0
        GAIN_9 RF (-9dB,0dB) 0
        GAIN_10 RF (-10dB,0dB) 0
        GAIN_11 RF (-11dB,0dB) 0
        GAIN_12 RF (-12dB,0dB) 0
        GAIN_13 RF (-13dB,0dB) 0
        GAIN_14 RF (-14dB,0dB) 0
        GAIN_15 RF (-15dB,0dB) 0
        GAIN_16 RF (-15dB,-1dB) 0
        GAIN_17 RF (-15dB,-2dB) 0
        GAIN_18 RF (-15dB,-3dB) 0
        GAIN_19 RF (-15dB,-4dB) 0
        GAIN_20 RF (-15dB,-5dB) 0
        GAIN_21 RF (-15dB,-6dB) 0
        GAIN_22 RF (-15dB,-7dB) 0
        GAIN_23 RF (-15dB,-8dB) 0
        GAIN_24 RF (-15dB,-9dB) 0
        GAIN_25 RF (-15dB,-10dB) 0
        GAIN_26 RF (-15dB,-11dB) 0
        GAIN_27 RF (-15dB,-12dB) 0
        GAIN_28 RF (-15dB,-13dB) 0
        GAIN_29 RF (-15dB,-14dB) 0
        GAIN_30 RF (-15dB,-15dB) 0
        GAIN_31 RF (-15dB,-15dB) 0
        GAIN_32 RF (-15dB,-15dB) 0
        GAIN_33 RF (-15dB,-15dB) 0
        GAIN_34 RF (-15dB,-15dB) 0
        GAIN_35 RF (-15dB,-15dB) 0
        GAIN_36 RF (-15dB,-15dB) 0
        GAIN_37 RF (-15dB,-15dB) 0
        GAIN_38 RF (-15dB,-15dB) 0
        GAIN_39 RF (-15dB,-15dB) 0
        GAIN_40 RF (-15dB,-15dB) 0
        GAIN_41 RF (-15dB,-15dB) 0
        GAIN_42 RF (-15dB,-15dB) 0
        GAIN_43 RF (-15dB,-15dB) 0
        GAIN_44 RF (-15dB,-15dB) 0
        GAIN_45 RF (-15dB,-15dB) 0
        GAIN_46 RF (-15dB,-15dB) 0
        GAIN_47 RF (-15dB,-15dB) 0
        GAIN_48 RF (-15dB,-15dB) 0
        GAIN_49 RF (-15dB,-15dB) 0
        GAIN_50 RF (-15dB,-15dB) 0
        GAIN_51 RF (-15dB,-15dB) 0
        GAIN_52 RF (-15dB,-15dB) 0
        GAIN_53 RF (-15dB,-15dB) 0
        GAIN_54 RF (-15dB,-15dB) 0
        GAIN_55 RF (-15dB,-15dB) 0
        GAIN_56 RF (-15dB,-15dB) 0
        GAIN_57 RF (-15dB,-15dB) 0
        GAIN_58 RF (-15dB,-15dB) 0
        GAIN_59 RF (-15dB,-15dB) 0
        GAIN_60 RF (-15dB,-15dB) 0
        GAIN_61 RF (-15dB,-15dB) 0
        GAIN_62 RF (-15dB,-15dB) 0
        GAIN_63 RF (-15dB,-15dB) 0
        GAIN_64 RF (-15dB,-15dB) 0
        GAIN_65 RF (-15dB,-15dB) 0
        GAIN_66 RF (0dB,0dB) 0"""

        tx.gain_table_config = gain_lut
        print("Gain Table written successfully")
        print(f"Gain Table Cfg readback:\n{tx.gain_table_config}")

