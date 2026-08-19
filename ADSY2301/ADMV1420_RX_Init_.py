# ==========================================================================
"""ADMV1420 Microwave Downconverter Example

Demonstrates configuration of the ADMV1420 receive downconverter using pyadi-iio.

The ADMV1420 converts RF signals to IF/baseband signals across four selectable
RF bands (0.1-2 GHz, 1-5 GHz, 3-13 GHz, 6-20 GHz). It includes digitally
selectable attenuators (DSAs), configurable LO sideband/filter, and on-chip
temperature and power sensors.

For standalone use, set the URI to the target device.
For Neponset board use, specify the device instance name (e.g., "admv1420_rx_0").
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
## Step 1: Initialize ADMV 1420 ##
##############################################
# talise_ip = "10.75.161.115"
# talise_ip = "10.75.161.140"
talise_ip = "10.75.161.150"
talise_uri = "ip:" + talise_ip

rx_0 = adi.admv1420(uri=talise_uri, device_name="admv1420_rx_0")
rx_1 = adi.admv1420(uri=talise_uri, device_name="admv1420_rx_1")
rx_2 = adi.admv1420(uri=talise_uri, device_name="admv1420_rx_2")
rx_3 = adi.admv1420(uri=talise_uri, device_name="admv1420_rx_3")

READCURRENTSTATE = True
WRITENEWSTATE = True
WRITELUTTABLES = False

if READCURRENTSTATE:
    for rx in [rx_0, rx_1, rx_2, rx_3]:
        # --- Read current configuration ---
        print("=== ADMV1420 Current Configuration ===")
        print(f"Device Name:              {rx._device_name}")
        print(f"RF Band:                  {rx.rf_band}")
        print(f"RF Band Avail:            {rx.rf_band_available}")
        print(f"RF DSA1 Gain:             {rx.rf_direct_dsa1_gain}")
        print(f"RF DSA1 Gain Avail:       {rx.rf_direct_dsa1_gain_available}")
        print(f"RF DSA2 Gain:             {rx.rf_direct_dsa2_gain}")
        print(f"RF DSA2 Gain Avail:       {rx.rf_direct_dsa2_gain_available}")
        print(f"RF DSA3 Gain:             {rx.rf_direct_dsa3_gain}")
        print(f"RF DSA3 Gain Avail:       {rx.rf_direct_dsa3_gain_available}")
        print(f"RF LPF:                   {rx.rf_direct_lpf_val}")
        print(f"RF HPF:                   {rx.rf_direct_hpf_val}")
        print(f"RF DSA1 Offset:           {rx.rf_direct_dsa1_offset}")
        print(f"RF DSA2 Offset:           {rx.rf_direct_dsa2_offset}")
        print(f"RF DSA3 Offset:           {rx.rf_direct_dsa3_offset}")
        print(f"RF Bypass LPF En:         {rx.rf_bypass_lpf_en}")
        print(f"RF Bypass LPF Val:        {rx.rf_bypass_lpf_val}")
        print(f"RF Bypass HPF En:         {rx.rf_bypass_hpf_en}")
        print(f"RF Bypass HPF Val:        {rx.rf_bypass_hpf_val}")
        print(f"RF Bypass DSA1 Gain:      {rx.rf_bypass_dsa1_gain}")
        print(f"RF Bypass DSA1 Avail:     {rx.rf_bypass_dsa1_gain_available}")
        print(f"RF Bypass DSA2 Gain:      {rx.rf_bypass_dsa2_gain}")
        print(f"RF Bypass DSA2 Avail:     {rx.rf_bypass_dsa2_gain_available}")
        print(f"RF Bypass DSA3 Gain:      {rx.rf_bypass_dsa3_gain}")
        print(f"RF Bypass DSA3 Avail:     {rx.rf_bypass_dsa3_gain_available}")

        print(f"\nIF Band:                  {rx.if_band}")
        print(f"IF Band Avail:            {rx.if_band_available}")
        print(f"IF Mode:                  {rx.if_mode}")
        print(f"IF Mode Avail:            {rx.if_mode_available}")
        print(f"IF DSA4 Gain:             {rx.if_direct_dsa4_gain}")
        print(f"IF DSA4 Gain Avail:       {rx.if_direct_dsa4_gain_available}")
        print(f"IF DSA5 Gain:             {rx.if_direct_dsa5_gain}")
        print(f"IF DSA5 Gain Avail:       {rx.if_direct_dsa5_gain_available}")
        print(f"IF LPF:                   {rx.if_direct_lpf_val}")
        print(f"IF DSA4 Offset:           {rx.if_direct_dsa4_offset}")
        print(f"IF DSA5 Offset:           {rx.if_direct_dsa5_offset}")
        print(f"IF DSA I 0.1dB:           {rx.if_dsai_0p1db}")
        print(f"IF DSA I 0.1dB Avail:     {rx.if_dsai_0p1db_available}")
        print(f"IF DSA Q 0.1dB:           {rx.if_dsaq_0p1db}")
        print(f"IF DSA Q 0.1dB Avail:     {rx.if_dsaq_0p1db_available}")
        print(f"IF Bypass LPF En:         {rx.if_bypass_lpf_en}")
        print(f"IF Bypass LPF Val:        {rx.if_bypass_lpf_val}")
        print(f"IF Bypass DSA4 Gain:      {rx.if_bypass_dsa4_gain}")
        print(f"IF Bypass DSA4 Avail:     {rx.if_bypass_dsa4_gain_available}")
        print(f"IF Bypass DSA5 Gain:      {rx.if_bypass_dsa5_gain}")
        print(f"IF Bypass DSA5 Avail:     {rx.if_bypass_dsa5_gain_available}")

        print(f"\nLO Sideband:              {rx.lo_sideband}")
        print(f"LO Sideband Avail:        {rx.lo_sideband_available}")
        print(f"LO x3 Filter:            {rx.lo_x3_filter}")
        print(f"LO x3 Filter Avail:      {rx.lo_x3_filter_available}")
        print(f"LO I Phase:               {rx.lo_direct_i_phase_val}")
        print(f"LO Q Phase:               {rx.lo_direct_q_phase_val}")

        # --- Read sensors ---
        print(f"\nTemperature:              {rx.temp_raw} (raw)")
        print(f"Power:                    {rx.power_raw} (raw)")

        # --- Direct register access (scratchpad test) ---
        print("\n=== Register Access ===")
        rx.reg_write(0x00A, 0xA5)
        val = rx.reg_read(0x00A)
        print(f"Scratchpad:     0x{int(val, 0):02X} (expected 0xA5)")

if WRITENEWSTATE:
    for rx in [rx_0, rx_1, rx_2, rx_3]:
        # --- Configure for 3-13 GHz RF band with IF output ---
        print("\n=== Configuring for 3-13 GHz band ===")
        rx.rf_band = "3GHz_13GHz"
        rx.if_band = "3GHz_13GHz"
        rx.if_mode = "if"
        rx.lo_sideband = "LSB"
        rx.lo_x3_filter = "14GHz_18GHz"

        # Set DSA gains to 0 dB (no attenuation)
        rx.rf_direct_dsa1_gain = "0dB"
        rx.rf_direct_dsa3_gain = "0dB"
        rx.if_direct_dsa4_gain = "0dB"
        rx.if_direct_dsa5_gain = "0dB"

        # Set DSA offsets
        rx.rf_direct_dsa1_offset = 0
        rx.rf_direct_dsa2_offset = 0
        rx.rf_direct_dsa3_offset = 0

        # Set LO phase
        rx.lo_direct_i_phase_val = 0
        rx.lo_direct_q_phase_val = 0

        # --- Read back configuration ---
        print(f"RF Band:        {rx.rf_band}")
        print(f"IF Band:        {rx.if_band}")
        print(f"IF Mode:        {rx.if_mode}")
        print(f"LO Sideband:    {rx.lo_sideband}")
        print(f"LO x3 Filter:  {rx.lo_x3_filter}")

        # --- Device-level attributes ---
        print(f"\n=== LUT Configuration ===")
        print(f"Filter Table:   {rx.filter_table_en}")
        print(f"Filter Load:    {rx.filter_load_en}")
        print(f"Filter Sel:     {rx.filter_table_sel}")
        print(f"Gain Table:     {rx.gain_table_en}")
        print(f"Gain Load:      {rx.gain_load_en}")
        print(f"Bypass Gain En: {rx.bypass_gain_table_en}")
        print(f"GPO_F:          {rx.direct_gpo_f}")
        print(f"GPO_G:          {rx.direct_gpo_g}")
        print(f"Bypass GPO_G:   {rx.bypass_gpo_g}")


        # --- Write and readback LUT table configurations ---

if WRITELUTTABLES:
    for rx in [rx_0, rx_1, rx_2, rx_3]:
        
        #LUTA_X RF (band,lpf,hpf,dsa1_off,dsa2_off,dsa3_off,gpo_f) IF (band,lpf,dsa4_off,dsa5_off,dsai,dsaq) LO (filter,sideband,i,q)
        print("\n=== Writing Filter Table A ===")
        filter_lut_a = """\
        LUTA_0 RF (100MHz_2GHz,0,0,0,0,0,0) IF (1GHz_5GHz,0,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTA_1 RF (1GHz_5GHz,0,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTA_2 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,3,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTA_3 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,1,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTA_4 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,0,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTA_5 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (10GHz_12GHz,USB,0,0)
        LUTA_6 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (10GHz_12GHz,USB,0,0)
        LUTA_7 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (10GHz_12GHz,USB,0,0)
        LUTA_8 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTA_9 RF (6GHz_20GHz,12,6,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTA_10 RF (6GHz_20GHz,12,6,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTA_11 RF (6GHz_20GHz,11,5,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTA_12 RF (6GHz_20GHz,11,5,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_13 RF (6GHz_20GHz,9,3,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_14 RF (6GHz_20GHz,9,3,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_15 RF (6GHz_20GHz,7,2,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_16 RF (6GHz_20GHz,7,2,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_17 RF (6GHz_20GHz,6,1,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_18 RF (6GHz_20GHz,6,1,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_19 RF (6GHz_20GHz,5,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTA_20 RF (6GHz_20GHz,5,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_21 RF (6GHz_20GHz,3,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_22 RF (6GHz_20GHz,3,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_23 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_24 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_25 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_26 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_27 RF (6GHz_20GHz,1,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_28 RF (6GHz_20GHz,1,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_29 RF (6GHz_20GHz,0,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_30 RF (6GHz_20GHz,0,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTA_31 RF (6GHz_20GHz,0,15,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)"""

        rx.filter_table_config_A = filter_lut_a
        print("Filter Table A written successfully")
        print(f"Filter Cfg A readback:\n{rx.filter_table_config_A}")

        #LUTB_X RF (band,lpf,hpf,dsa1_off,dsa2_off,dsa3_off,gpo_f) IF (band,lpf,dsa4_off,dsa5_off,dsai,dsaq) LO (filter,sideband,i,q)
        print("\n=== Writing Filter Table B ===")
        filter_lut_b = """\
        LUTB_0 RF (100MHz_2GHz,0,0,0,0,0,0) IF (1GHz_5GHz,0,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTB_1 RF (1GHz_5GHz,0,0,0,0,0,0) IF (1GHz_5GHz,2,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTB_2 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,3,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTB_3 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,1,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTB_4 RF (3GHz_13GHz,0,0,0,0,0,0) IF (3GHz_13GHz,0,0,0,0dB,0dB) LO (24GHz_28GHz,LSB,0,0)
        LUTB_5 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTB_6 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTB_7 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (12GHz_14GHz,USB,0,0)
        LUTB_8 RF (6GHz_20GHz,15,15,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_9 RF (6GHz_20GHz,12,6,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_10 RF (6GHz_20GHz,12,6,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_11 RF (6GHz_20GHz,11,5,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_12 RF (6GHz_20GHz,11,5,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_13 RF (6GHz_20GHz,9,3,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_14 RF (6GHz_20GHz,9,3,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_15 RF (6GHz_20GHz,7,2,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (14GHz_18GHz,USB,0,0)
        LUTB_16 RF (6GHz_20GHz,7,2,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_17 RF (6GHz_20GHz,6,1,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_18 RF (6GHz_20GHz,6,1,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_19 RF (6GHz_20GHz,5,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_20 RF (6GHz_20GHz,5,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_21 RF (6GHz_20GHz,3,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_22 RF (6GHz_20GHz,3,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_23 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_24 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_25 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_26 RF (6GHz_20GHz,2,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_27 RF (6GHz_20GHz,1,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)
        LUTB_28 RF (6GHz_20GHz,1,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (24GHz_28GHz,USB,0,0)
        LUTB_29 RF (6GHz_20GHz,0,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (24GHz_28GHz,USB,0,0)
        LUTB_30 RF (6GHz_20GHz,0,0,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (24GHz_28GHz,USB,0,0)
        LUTB_31 RF (6GHz_20GHz,0,15,0,0,0,0) IF (1GHz_5GHz,1,0,0,0dB,0dB) LO (18GHz_24GHz,USB,0,0)"""

        rx.filter_table_config_B = filter_lut_b
        print("Filter Table B written successfully")
        print(f"Filter Cfg B readback:\n{rx.filter_table_config_B}")

        #GAIN_X RF (dsa1,dsa2,dsa3) IF (dsa4,dsa5) gpo_g
        print("\n=== Writing Gain Table ===")
        gain_lut = """\
        GAIN_0 RF (0dB,0dB,0dB) IF (0dB,0dB) 0
        GAIN_1 RF (0dB,0dB,0dB) IF (0dB,-1dB) 0
        GAIN_2 RF (0dB,0dB,0dB) IF (0dB,-2dB) 0
        GAIN_3 RF (0dB,0dB,0dB) IF (0dB,-3dB) 0
        GAIN_4 RF (0dB,0dB,0dB) IF (0dB,-4dB) 0
        GAIN_5 RF (0dB,0dB,0dB) IF (0dB,-5dB) 0
        GAIN_6 RF (0dB,0dB,0dB) IF (0dB,-6dB) 0
        GAIN_7 RF (0dB,0dB,0dB) IF (0dB,-7dB) 0
        GAIN_8 RF (0dB,0dB,0dB) IF (0dB,-8dB) 0
        GAIN_9 RF (0dB,0dB,0dB) IF (0dB,-9dB) 0
        GAIN_10 RF (0dB,0dB,0dB) IF (0dB,-10dB) 0
        GAIN_11 RF (0dB,0dB,0dB) IF (0dB,-11dB) 0
        GAIN_12 RF (0dB,0dB,0dB) IF (0dB,-12dB) 0
        GAIN_13 RF (0dB,0dB,0dB) IF (0dB,-13dB) 0
        GAIN_14 RF (0dB,0dB,0dB) IF (0dB,-14dB) 0
        GAIN_15 RF (0dB,0dB,0dB) IF (0dB,-15dB) 0
        GAIN_16 RF (0dB,0dB,0dB) IF (-1dB,-15dB) 0
        GAIN_17 RF (0dB,0dB,0dB) IF (-2dB,-15dB) 0
        GAIN_18 RF (0dB,0dB,0dB) IF (-3dB,-15dB) 0
        GAIN_19 RF (0dB,0dB,0dB) IF (-4dB,-15dB) 0
        GAIN_20 RF (0dB,0dB,0dB) IF (-5dB,-15dB) 0
        GAIN_21 RF (0dB,0dB,0dB) IF (-6dB,-15dB) 0
        GAIN_22 RF (0dB,0dB,0dB) IF (-7dB,-15dB) 0
        GAIN_23 RF (0dB,0dB,0dB) IF (-8dB,-15dB) 0
        GAIN_24 RF (0dB,0dB,0dB) IF (-9dB,-15dB) 0
        GAIN_25 RF (0dB,0dB,0dB) IF (-10dB,-15dB) 0
        GAIN_26 RF (0dB,0dB,0dB) IF (-11dB,-15dB) 0
        GAIN_27 RF (0dB,0dB,0dB) IF (-12dB,-15dB) 0
        GAIN_28 RF (0dB,0dB,0dB) IF (-13dB,-15dB) 0
        GAIN_29 RF (0dB,0dB,0dB) IF (-14dB,-15dB) 0
        GAIN_30 RF (0dB,0dB,0dB) IF (-15dB,-15dB) 0
        GAIN_31 RF (0dB,0dB,-1dB) IF (-15dB,-15dB) 0
        GAIN_32 RF (0dB,0dB,-2dB) IF (-15dB,-15dB) 0
        GAIN_33 RF (0dB,0dB,-3dB) IF (-15dB,-15dB) 0
        GAIN_34 RF (0dB,0dB,-4dB) IF (-15dB,-15dB) 0
        GAIN_35 RF (0dB,0dB,-5dB) IF (-15dB,-15dB) 0
        GAIN_36 RF (0dB,0dB,-6dB) IF (-15dB,-15dB) 0
        GAIN_37 RF (0dB,0dB,-7dB) IF (-15dB,-15dB) 0
        GAIN_38 RF (0dB,0dB,-8dB) IF (-15dB,-15dB) 0
        GAIN_39 RF (0dB,0dB,-9dB) IF (-15dB,-15dB) 0
        GAIN_40 RF (0dB,0dB,-10dB) IF (-15dB,-15dB) 0
        GAIN_41 RF (0dB,0dB,-11dB) IF (-15dB,-15dB) 0
        GAIN_42 RF (0dB,0dB,-12dB) IF (-15dB,-15dB) 0
        GAIN_43 RF (0dB,0dB,-13dB) IF (-15dB,-15dB) 0
        GAIN_44 RF (0dB,0dB,-14dB) IF (-15dB,-15dB) 0
        GAIN_45 RF (0dB,0dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_46 RF (0dB,-6dB,-10dB) IF (-15dB,-15dB) 0
        GAIN_47 RF (0dB,-6dB,-11dB) IF (-15dB,-15dB) 0
        GAIN_48 RF (0dB,-6dB,-12dB) IF (-15dB,-15dB) 0
        GAIN_49 RF (0dB,-6dB,-13dB) IF (-15dB,-15dB) 0
        GAIN_50 RF (0dB,-6dB,-14dB) IF (-15dB,-15dB) 0
        GAIN_51 RF (0dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_52 RF (-1dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_53 RF (-2dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_54 RF (-3dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_55 RF (-4dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_56 RF (-5dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_57 RF (-6dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_58 RF (-7dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_59 RF (-8dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_60 RF (-9dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_61 RF (-10dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_62 RF (-11dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_63 RF (-12dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_64 RF (-13dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_65 RF (-14dB,-6dB,-15dB) IF (-15dB,-15dB) 0
        GAIN_66 RF (-15dB,-6dB,-15dB) IF (-15dB,-15dB) 0"""

        rx.gain_table_config = gain_lut
        print("Gain Table written successfully")
        print(f"Gain Table Cfg readback:\n{rx.gain_table_config}")


