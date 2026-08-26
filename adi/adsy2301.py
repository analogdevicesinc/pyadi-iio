# ==========================================================================
# ADSY2301 — 64-Element Phased-Array Helper Functions
# --------------------------------------------------------------------------
# This module provides channel enable/disable, calibration (gain, phase,
# digital NCO), beam steering utilities, and FFT analysis routines for the
# ADSY2301 evaluation system.
#
# Hardware:
#   - 16 x ADAR1000 beamformer ICs (64 antenna elements)
#   - ADRV9009-ZU11EG dual transceiver SoM
#   - ADF4371 on-board LO PLL
#   - ADXUD1AEBZ up/down-converter
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import time
import warnings
import importlib
import adi
from adi.adar1000 import adar1000_array
from adi.adf4382 import adf4382
from adi.admv1320 import admv1320
from adi.admv1420 import admv1420
from adi.adrv9009_zu11eg import adrv9009_zu11eg
import matplotlib.pyplot as plt
import numpy as np
import genalyzer as gn
import re
import json
import os
from adi.attribute import attribute
from adi.context_manager import context_manager



class adsy2301(adar1000_array,context_manager):
    """ADSY2301 Beamforming System Interface

    This class is a generic interface for boards that utilizes ADAR1000 Array Class
    along with a lot of other devices.

    parameters:
        uri: type=string
            URI of IIO context with ADAR1000 array
        chip_ids: type=list[string]
            List of strings identifying desired chip select and hardware ID
            for the ADAR1000. These strings are the labels coinciding with
            each chip select and hardware address and are typically in the
            form csbX_chipX. The csb line can be any number depending on how
            many are used in the system. The chip number will typically be
            1-4 because each CSB line can control up to four ADAR1000s. Note
            that the order of the devices listed will correspond to the
            device numbers in the array map directly.
        device_map: type=list[list[int]]
            List with the map of where the ADAR1000s are in the array. Each
            entry in the map represents a row of ADAR1000s referenced by
            device number. For example, a map:

                | [[1, 3, 5, 7],
                | [2, 4, 6, 8]]

            represents an array of 8 ADAR1000s 4 wide and 2 tall.
        element_map: type=list[list[int]]
            List of lists with the map of where the array elements are in the
            physical array. Each entry in the map represents a row of array
            channels referenced by element number. For example, a map:

                | [[1, 5, 9, 13],
                | [2, 6, 10, 14],
                | [3, 7, 11, 15],
                | [4, 8, 12, 16]]

            represents an array of 16 elements (4 ADAR1000s) in a square array.
        device_element_map: type=dict[int, list[int]]
            Dictionary with the map of ADAR1000 to array element references. Each
            key in the map is a device number. The corresponding list of integers
            represents the array element numbers connected to that ADAR1000, in
            order of the ADAR1000's channels. For example, an entry of
            {3: [10, 14, 13, 9]} connects ADAR1000 #3 to array elements 10, 14, 13,
            and 9. Element #10 is on the ADAR1000's channel 1 while element #13 is
            on the ADAR1000's channel 3.
    """
    _device_name = ""

    def __init__(self, uri=""):
        self.uri = uri
        self._available = []
        context_manager.__init__(self, uri, self._device_name)
        self.udc = self.UDC(self.uri, self._ctx)

    class BFC_Array(adar1000_array):
        def __init__(self, uri="", chip_ids=None, device_map=None,
                    element_map=None, device_element_map=None):
            adar1000_array.__init__(
                self,
                uri=uri,
                chip_ids=chip_ids,
                device_map=device_map,
                element_map=element_map,
                device_element_map=device_element_map,
            )
            self._pwr_channels = {}
            artix_control_1 = self._ctx.find_device("mantaray_pwr_control")
            pwr_labels = [
                "BF_PWR_EN_01", "BF_PWR_EN_02", "BF_PWR_EN_03", "BF_PWR_EN_04"
            ]
            for channel in artix_control_1.channels:
                if "label" in channel.attrs:
                    label = channel.attrs["label"].value
                    if label in pwr_labels:
                        self._pwr_channels[label] = artix_control_1.find_channel(channel.id, True)
                        
            self._pa_ctrl_channels = {}
            artix_control_2 = self._ctx.find_device("mantaray_control")
            pa_labels = [
                "BF_PA_ON_01", "BF_PA_ON_02", "BF_PA_ON_03", "BF_PA_ON_04"
            ]
            for channel in artix_control_2.channels:
                if "label" in channel.attrs:
                    label = channel.attrs["label"].value
                    if label in pa_labels:
                        self._pa_ctrl_channels[label] = artix_control_2.find_channel(channel.id, True)
        @property
        def BF_PWR_EN_01(self):
            return int(self._pwr_channels["BF_PWR_EN_01"].attrs["raw"].value)
        @BF_PWR_EN_01.setter
        def BF_PWR_EN_01(self, value):
            self._pwr_channels["BF_PWR_EN_01"].attrs["raw"].value = str(value)
        @property
        def BF_PWR_EN_02(self):
            return int(self._pwr_channels["BF_PWR_EN_02"].attrs["raw"].value)
        @BF_PWR_EN_02.setter
        def BF_PWR_EN_02(self, value):
            self._pwr_channels["BF_PWR_EN_02"].attrs["raw"].value = str(value)
        @property
        def BF_PWR_EN_03(self):
            return int(self._pwr_channels["BF_PWR_EN_03"].attrs["raw"].value)
        @BF_PWR_EN_03.setter
        def BF_PWR_EN_03(self, value):
            self._pwr_channels["BF_PWR_EN_03"].attrs["raw"].value = str(value)
        @property
        def BF_PWR_EN_04(self):
            return int(self._pwr_channels["BF_PWR_EN_04"].attrs["raw"].value)
        @BF_PWR_EN_04.setter
        def BF_PWR_EN_04(self, value):
            self._pwr_channels["BF_PWR_EN_04"].attrs["raw"].value = str(value)

        @property
        def BF_PA_ON_01(self):
            return int(self._pa_ctrl_channels["BF_PA_ON_01"].attrs["raw"].value)
        @BF_PA_ON_01.setter
        def BF_PA_ON_01(self, value):
            self._pa_ctrl_channels["BF_PA_ON_01"].attrs["raw"].value = str(value)
        @property
        def BF_PA_ON_02(self):
            return int(self._pa_ctrl_channels["BF_PA_ON_02"].attrs["raw"].value)
        @BF_PA_ON_02.setter
        def BF_PA_ON_02(self, value):
            self._pa_ctrl_channels["BF_PA_ON_02"].attrs["raw"].value = str(value)
        @property
        def BF_PA_ON_03(self):
            return int(self._pa_ctrl_channels["BF_PA_ON_03"].attrs["raw"].value)
        @BF_PA_ON_03.setter
        def BF_PA_ON_03(self, value):
            self._pa_ctrl_channels["BF_PA_ON_03"].attrs["raw"].value = str(value)
        @property
        def BF_PA_ON_04(self):
            return int(self._pa_ctrl_channels["BF_PA_ON_04"].attrs["raw"].value)
        @BF_PA_ON_04.setter
        def BF_PA_ON_04(self, value):
            self._pa_ctrl_channels["BF_PA_ON_04"].attrs["raw"].value = str(value)


    class UDC():
        def __init__(self, uri, ctx):
            self.uri = uri
            self._ctx = ctx
            self._available = []

        class ADMV8913:
            def __init__(self, ctx):
                self._channels = {}
                artix_control = ctx.find_device("mantaray_control")
                labels = [
                    "RF_FL_HPF0", "RF_FL_HPF1", "RF_FL_HPF2", "RF_FL_HPF3",
                    "RF_FL_LPF0", "RF_FL_LPF1", "RF_FL_LPF2", "RF_FL_LPF3",
                ]
                for channel in artix_control.channels:
                    label = channel.attrs["label"].value
                    if label in labels:
                        self._channels[label] = artix_control.find_channel(channel.id, True)

            @property
            def RF_FL_HPF0(self):
                return int(self._channels["RF_FL_HPF0"].attrs["raw"].value)
            @RF_FL_HPF0.setter
            def RF_FL_HPF0(self, value):
                self._channels["RF_FL_HPF0"].attrs["raw"].value = str(value)
            @property
            def RF_FL_HPF1(self):
                return int(self._channels["RF_FL_HPF1"].attrs["raw"].value)
            @RF_FL_HPF1.setter
            def RF_FL_HPF1(self, value):
                self._channels["RF_FL_HPF1"].attrs["raw"].value = str(value)
            @property
            def RF_FL_HPF2(self):
                return int(self._channels["RF_FL_HPF2"].attrs["raw"].value)
            @RF_FL_HPF2.setter
            def RF_FL_HPF2(self, value):
                self._channels["RF_FL_HPF2"].attrs["raw"].value = str(value)
            @property
            def RF_FL_HPF3(self):
                return int(self._channels["RF_FL_HPF3"].attrs["raw"].value)
            @RF_FL_HPF3.setter
            def RF_FL_HPF3(self, value):
                self._channels["RF_FL_HPF3"].attrs["raw"].value = str(value)
            @property
            def RF_FL_LPF0(self):
                return int(self._channels["RF_FL_LPF0"].attrs["raw"].value)
            @RF_FL_LPF0.setter
            def RF_FL_LPF0(self, value):
                self._channels["RF_FL_LPF0"].attrs["raw"].value = str(value)
            @property
            def RF_FL_LPF1(self):
                return int(self._channels["RF_FL_LPF1"].attrs["raw"].value)
            @RF_FL_LPF1.setter
            def RF_FL_LPF1(self, value):
                self._channels["RF_FL_LPF1"].attrs["raw"].value = str(value)
            @property
            def RF_FL_LPF2(self):
                return int(self._channels["RF_FL_LPF2"].attrs["raw"].value)
            @RF_FL_LPF2.setter
            def RF_FL_LPF2(self, value):
                self._channels["RF_FL_LPF2"].attrs["raw"].value = str(value)
            @property
            def RF_FL_LPF3(self):
                return int(self._channels["RF_FL_LPF3"].attrs["raw"].value)
            @RF_FL_LPF3.setter
            def RF_FL_LPF3(self, value):
                self._channels["RF_FL_LPF3"].attrs["raw"].value = str(value)

            @property
            def all_settings(self):
                return {name: int(ch.attrs["raw"].value) for name, ch in self._channels.items()}

            def set_filter_settings(self, hp_freq, lp_freq):

                HPF_state = int((hp_freq/1e9 - 6.4) / 0.333 + 0.5)
                LPF_state = int((lp_freq/1e9 - 7.2) / 0.34 + 0.5)
                hpf_actual = 6.4 + HPF_state * 0.333
                lpf_actual = 7.2 + LPF_state * 0.34

                print(f"Requested: HPF = {hp_freq/1e9} GHz, LPF = {lp_freq/1e9} GHz")
                print(f"Nearest: HPF = {hpf_actual:.1f} GHz (state {HPF_state}), "
                    f"LPF = {lpf_actual:.1f} GHz (state {LPF_state})")
                
                hpf_bits = [(HPF_state >> i) & 1 for i in range(4)]
                lpf_bits = [(LPF_state >> i) & 1 for i in range(4)]

                print(f"Setting HPF bits: B3={hpf_bits[3]} B2={hpf_bits[2]} "
                    f"B1={hpf_bits[1]} B0={hpf_bits[0]}")
                
                self.RF_FL_HPF0 = hpf_bits[0]
                self.RF_FL_HPF1 = hpf_bits[1]
                self.RF_FL_HPF2 = hpf_bits[2]
                self.RF_FL_HPF3 = hpf_bits[3]

                print(f"Setting LPF bits: B3={lpf_bits[3]} B2={lpf_bits[2]} "
                    f"B1={lpf_bits[1]} B0={lpf_bits[0]}")
                
                self.RF_FL_LPF0 = lpf_bits[0]
                self.RF_FL_LPF1 = lpf_bits[1]
                self.RF_FL_LPF2 = lpf_bits[2]
                self.RF_FL_LPF3 = lpf_bits[3]

                print(f"Readback: HPF={self.RF_FL_HPF3}{self.RF_FL_HPF2}{self.RF_FL_HPF1}{self.RF_FL_HPF0} "
                    f"LPF={self.RF_FL_LPF3}{self.RF_FL_LPF2}{self.RF_FL_LPF1}{self.RF_FL_LPF0}")

            def set_filter_band1(self):
                self.set_filter_settings(7.732e9, 9.58e9)

            def set_filter_band2(self):
                self.set_filter_settings(8.4e9, 10.26e9)

            def set_filter_band3(self):
                self.set_filter_settings(9.4e9, 11.28e9)

            def set_filter_band4(self):
                self.set_filter_settings(10.4e9, 11.96e9)

            def set_filter_widest(self):
                self.set_filter_settings(6.4e9, 12.3e9)

        class ADRF5030:
            def __init__(self, ctx):
                self._channels = {}
                switch = ctx.find_device("mantaray_txrx_control")
                labels = [
                    "ADRF5030_CTRL1", "ADRF5030_CTRL2", "ADRF5030_CTRL3", "ADRF5030_CTRL4",
                    "ADRF5030_EN1", "ADRF5030_EN2", "ADRF5030_EN3", "ADRF5030_EN4",
                ]
                for channel in switch.channels:
                    label = channel.attrs["label"].value
                    if label in labels:
                        self._channels[label] = switch.find_channel(channel.id, True)

            @property
            def ADRF5030_CTRL1(self):
                return int(self._channels["ADRF5030_CTRL1"].attrs["raw"].value)
            @ADRF5030_CTRL1.setter
            def ADRF5030_CTRL1(self, value):
                self._channels["ADRF5030_CTRL1"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_CTRL2(self):
                return int(self._channels["ADRF5030_CTRL2"].attrs["raw"].value)
            @ADRF5030_CTRL2.setter
            def ADRF5030_CTRL2(self, value):
                self._channels["ADRF5030_CTRL2"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_CTRL3(self):
                return int(self._channels["ADRF5030_CTRL3"].attrs["raw"].value)
            @ADRF5030_CTRL3.setter
            def ADRF5030_CTRL3(self, value):
                self._channels["ADRF5030_CTRL3"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_CTRL4(self):
                return int(self._channels["ADRF5030_CTRL4"].attrs["raw"].value)
            @ADRF5030_CTRL4.setter
            def ADRF5030_CTRL4(self, value):
                self._channels["ADRF5030_CTRL4"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_EN1(self):
                return int(self._channels["ADRF5030_EN1"].attrs["raw"].value)
            @ADRF5030_EN1.setter
            def ADRF5030_EN1(self, value):
                self._channels["ADRF5030_EN1"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_EN2(self):
                return int(self._channels["ADRF5030_EN2"].attrs["raw"].value)
            @ADRF5030_EN2.setter
            def ADRF5030_EN2(self, value):
                self._channels["ADRF5030_EN2"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_EN3(self):
                return int(self._channels["ADRF5030_EN3"].attrs["raw"].value)
            @ADRF5030_EN3.setter
            def ADRF5030_EN3(self, value):
                self._channels["ADRF5030_EN3"].attrs["raw"].value = str(value)

            @property
            def ADRF5030_EN4(self):
                return int(self._channels["ADRF5030_EN4"].attrs["raw"].value)
            @ADRF5030_EN4.setter
            def ADRF5030_EN4(self, value):
                self._channels["ADRF5030_EN4"].attrs["raw"].value = str(value)

            @property
            def all_settings(self):
                return {name: int(ch.attrs["raw"].value) for name, ch in self._channels.items()}
            
            # --- TX Switch Functions ---
            def TX_SW_Enable(self):
                for i in range(1, 5):
                    setattr(self, f"ADRF5030_EN{i}", 0)
                    setattr(self, f"ADRF5030_CTRL{i}", 1)
                print(f"TX_All: {self.all_settings}")

            # --- RX Switch Functions ---

            def RX_SW_Enable(self):
                for i in range(1, 5):
                    setattr(self, f"ADRF5030_EN{i}", 0)
                    setattr(self, f"ADRF5030_CTRL{i}", 0)
                print(f"RX_All: {self.all_settings}")

        def init_ADMV1320(self,device_names=None):
            uri = self.uri
            device_names = device_names or [
                "admv1320_tx_0",
                "admv1320_tx_1",
                "admv1320_tx_2",
                "admv1320_tx_3",
            ]
            try:
                self.admv1320 = [admv1320(uri=uri, device_name=name) for name in device_names]
                self._available.append("ADMV130")
                print(f"ADMV1320 context found: {len(self.admv1320)} devices")
            except Exception as e:
                warnings.warn(f"Skipping: {e}", UserWarning, stacklevel=2)

        def init_ADMV1420(self,device_names=None):
            uri = self.uri
            device_names = device_names or [
                "admv1420_rx_0",
                "admv1420_rx_1",
                "admv1420_rx_2",
                "admv1420_rx_3",
            ]
            try:
                self.admv1420 = [admv1420(uri=uri, device_name=name) for name in device_names]
                self._available.append("ADMV1420")
                print(f"ADMV1420 context found: {len(self.admv1420)} devices")
            except Exception as e:
                warnings.warn(f"Skipping: {e}", UserWarning, stacklevel=2)

        def init_ADF4382(self,device_name=None):
            uri = self.uri
            device_name = device_name or "adf4382a"

            try:
                #initialize the ADF4382 LO class
                self.adf4382 = adf4382(uri=uri, device_name=device_name)
                self._available.append("ADF4382")
                self.adf4382.altvolt0_en = 1
                self.adf4382.altvolt1_en = 1
                print(f"ADF4382 context found")

            except Exception as e:
                warnings.warn(f"Skipping: {e}", UserWarning, stacklevel=2)

        def init_ADMV8913(self):
            try:
                self.admv8913 = self.ADMV8913(self._ctx)
                self._available.append("ADMV8913")
                print("ADMV8913 context found")
            except Exception as e:
                warnings.warn(f"ADMV8913: {e}", UserWarning)
                self.admv8913 = None

        def init_ADRF5030(self):
            try:
                self.adrf5030 = self.ADRF5030(self._ctx)
                self._available.append("adrf5030")
                print("ADRF5030 Switches context found")
            except Exception as e:
                warnings.warn(f"ADRF5030: {e}", UserWarning)
                self.admv8913 = None

        def RX_UDC_Band_0(self):
            print("\n=== Configuring for 3-13 GHz IF band ===")
            for rx in self.admv1420:
                # --- Configure for 3-13 GHz RF band with IF output ---
                print(rx._device_name)
                rx.rf_band = "6GHz_20GHz"
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
                rx.rf_direct_dsa3_offset = 5

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

        def TX_UDC_Band_0(self):
            print("\n=== Configuring for 3-13 GHz IF band ===")
            for tx in self.admv1320:
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


    def init_BFC(self, chip_ids, device_map=None, element_map=None, device_element_map=None):
        try:
            self.BFC = self.BFC_Array(
                uri=self.uri,
                chip_ids=chip_ids,
                device_map=device_map,
                element_map=element_map,
                device_element_map=device_element_map,
            )
            
            self._available.append("BFC")
            print("BFC context found")
        except Exception as e:
            warnings.warn(f"Skipping: {e}", UserWarning, stacklevel=2)
            result = None

    def init_ADRV9009(self):
        try:
            self.ADRV9009 = adrv9009_zu11eg(
                uri=self.uri,
            )
            self._available.append("ADRV9009")
            print("ADRV9009 context found")
        except Exception as e:
            warnings.warn(f"Skipping: {e}", UserWarning, stacklevel=2)
            result = None

    def init_UDC(self):
        try:
            self.udc.init_ADMV8913()
            self.udc.init_ADRF5030()
            self.udc.init_ADF4382()
            self.udc.init_ADMV1320()
            self.udc.init_ADMV1420()

        except Exception as e:
            warnings.warn(f"Could not initalize one or more devices in UDC: {e}", UserWarning)
            self.udc = None


def enable_rx_channel(obj, elements=None, man_input=False):
    """
    Enables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn on (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    elif man_input is False and elements is None:
        elements = elements=list(range(1,65))

    else:
        elements = np.array(elements).flatten()

    for i in range(10):
        try:
            for device in obj.devices.values():
                # time.sleep(0.01)
                if device.mode == "rx":
                    for channel in device.channels:
                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                # print("Turning on element:",elem)
                                channel.rx_enable = True
                                device.lna_bias_on = -0.9412
                                        
                else:
                    raise ValueError('Mode of operation must be either "rx"')
            break
        except:
            print("retrying")
            time.sleep(0.5)

# Receive data on ADRV9009
def data_capture(adc):
    adc.rx_destroy_buffer() # clear previous data
    for i in range(2):
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    
    return data

def disable_tx_channel(obj, elements=None):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """

    if elements is None:
        elements = elements=list(range(1,65))

    else:
        elements = np.array(elements).flatten()

    # --- optimized: build set for O(1) membership and iterate channels once ---
    elements_set = set(int(x) for x in elements)

    # perform operations per device, iterating channels only once
    for device in obj.devices.values():
        time.sleep(0.01)
        # if device.mode == "tx":
        gate_voltage_bias = -4.8
        tol = 0.1 * abs(gate_voltage_bias)
        tries = 3
        for channel in device.channels:
            str_channel = str(channel)
            value = int(strip_to_last_two_digits(str_channel))
            if value in elements_set:
                # disable TX and set bias
                channel.tx_enable = False
                channel.pa_bias_on = gate_voltage_bias
                obj.latch_tx_settings()
                # verify setting within tolerance with short retries
                for _ in range(tries):
                    if abs(channel.pa_bias_on - gate_voltage_bias) <= tol:
                        break
                    time.sleep(0.05)
                else:
                    print(f"Not set properly: channel.pa_bias_on={channel.pa_bias_on}")
                    print(f"Element number {value}")
 
def enable_tx_channel(obj, elements=None,PA_Bias_Dict=None, gate_voltage_bias = -1.8):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """

    if elements is None:
        print("No elements Specified, please provide element indicies to enable PAs")
        return

    elif PA_Bias_Dict is not None:
        elements = np.array(elements).flatten()
        # --- optimized: build set for O(1) membership and iterate channels once ---
        elements_set = set(int(x) for x in elements)

        # perform operations per device, iterating channels only once
        for device in obj.devices.values():
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                tol = 0.1 * PA_Bias_Dict[value]
                tries = 3
                if value in elements_set:
                    # disable TX and set bias
                    channel.tx_enable = True
                    channel.pa_bias_on = PA_Bias_Dict[value]
                    obj.latch_tx_settings()
                    # verify setting within tolerance with short retries
                    for _ in range(tries):
                        if abs(channel.pa_bias_on - PA_Bias_Dict[value]) <= tol:
                            break
                        time.sleep(0.05)
                    else:
                        print(f"Not set properly: channel.pa_bias_on={channel.pa_bias_on}")
                        print(f"Element number {value}")
    else:
        elements = np.array(elements).flatten()

        # --- optimized: build set for O(1) membership and iterate channels once ---
        elements_set = set(int(x) for x in elements)

        # perform operations per device, iterating channels only once
        for device in obj.devices.values():
            # gate_voltage_bias = -2.0
            tol = 0.1 * abs(gate_voltage_bias)
            tries = 3
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                if value in elements_set:
                    # disable TX and set bias
                    channel.tx_enable = True
                    channel.pa_bias_on = gate_voltage_bias
                    obj.latch_tx_settings()
                    # verify setting within tolerance with short retries
                    for _ in range(tries):
                        if abs(channel.pa_bias_on - gate_voltage_bias) <= tol:
                            break
                        time.sleep(0.05)
                    else:
                        print(f"Not set properly: channel.pa_bias_on={channel.pa_bias_on}")
                        print(f"Element number {value}")

def manta_power_detector(obj, elements, man_input=False):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn off (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    elif man_input is False and elements is None:
        print("No elements Specified, please provide element indicies to enable PAs")
        return

    else:
        elements = np.array(elements).flatten()

    for elem in elements:
        tries = 10
        for device in obj.devices.values():
            time.sleep(0.01)
            for channel in device.channels:

                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))

                # Check if the channel is in the list of elements to disable
                # If it is, disable the channel

                if elem == value:
                    channel._detector_enable = True
                    if channel._detector_enable != True:
                        found = False
                        for _ in range(tries):
                            if channel._detector_enable != True:
                                pass
                            else:
                                found = True
                                break
                        if not found:
                            print(f"Not set properly: {channel._detector_enable=}")
                            print(f"Element number {channel}")
                    return(channel.detector_power)

def disable_rx_channel(obj, elements=None, man_input=False):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn off (1-64): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 64]

    elif man_input is False and elements is None:
        elements = elements=list(range(1,65))

    else:
        elements = np.array(elements).flatten()

    for i in range(10):
        try:
            for device in obj.devices.values():
                # print(device.mode)
                time.sleep(0.01)
                if device.mode == "tx":
                    for channel in device.channels:

                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        tries = 3
                        for elem in elements:
                            if elem == value:
                                channel.tx_enable = True
                                channel.pa_bias_on = -4.6
                                if round(channel.pa_bias_on,1) != -4.6:
                                    found = False
                                    for _ in range(tries):
                                        if round(channel.pa_bias_on,1) != -4.6:
                                            pass
                                        else:
                                            found = True
                                            break
                                    if not found:
                                        print(f"Not set properly: {channel.pa_bias_on=}")
                                        print(f"Element number {channel}")

                elif device.mode == "rx":
                    for channel in device.channels:
                        str_channel = str(channel)
                        value = int(strip_to_last_two_digits(str_channel))

                        # Check if the channel is in the list of elements to disable
                        # If it is, disable the channel
                        for elem in elements:
                            if elem == value:
                                # print("Turning off element:",elem)
                                channel.rx_enable = False
                                device.lna_bias_on = -4.8
                                break
                else:
                    raise ValueError('Mode of operation must be either "rx" or "tx"')
            break
        except:
            print("retrying")
            time.sleep(2)
    else:
        raise ValueError('Mode of operation must be either "rx" or "tx"')
        
# Receive data on ADRV9009
def data_capture_cal(adc, cal_values):
    adc.rx_destroy_buffer() # clear previous data
    for i in range(2):
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    data = cal_data(data, cal_values) # only do phase delay cals, no gain
    return data
 
# Add phasor with delay to complex data
def phase_delayer(data, delay):
    # Adds phase delay in degrees
    delayed_data = data * np.exp(1j*np.deg2rad(delay))
    return delayed_data

# Calibrate the data using phase and gain calibration values
def cal_data(data, phaseCAL):
    for i in range(len(data)):
        #data[i] = phase_delayer(data[i]*gainCal[i], phaseCAL[i])
        data[i] = phase_delayer(data[i], phaseCAL[i])
    return data

def gain_codes(obj, analog_mag_pre_cal, mode):
    """array.
    gainCodes  Determines Rx/Tx analog VGA gain codes for Stingray
    Help: returns calibrated gain codes and attenuation values.
    """
    atten = np.zeros(np.shape(analog_mag_pre_cal))
   
    # Polynomial fit coefficients for Rx and Tx modes
    if mode == "rx":
        poly_atten1 = [-4.178368227245296e-09, -3.124456767699238e-07, -7.218061870232358e-06,
                     1.146280656652001e-05, 0.003079353177989, 0.048281159204065,
                     0.247215102895886, 0.176811045216789, 10.163992861226674, 127.1237461140638]
        poly_atten0 = [4.12957161960063e-10, 1.11191262836380e-07, 1.34714959988008e-05,
                     0.000967813015434471, 0.0456701602403594, 1.47865205676699,
                     33.2281071820574, 510.768971360134, 5126.75849430329, 30268.0388934082, 79815.3362477404]
    elif mode == "tx":
        poly_atten1 = [2.11066024918707e-11, 5.70009839945272e-09, 5.49937839434060e-07,
                     2.73783996444945e-05, 0.000800103462132557, 0.0143895847100511,
                     0.159688022065331, 1.06808692792217, 4.50865732789487,
                     21.0313863981928, 127.541504127078]
        poly_atten0 = [5.00901188825329e-10, 1.44673726954726e-07, 1.86493751074489e-05,
                     0.00141263342869073, 0.0696128076080524, 2.33122230277517,
                     53.7090182591208, 840.244043642996, 8539.25517554357,    
                     50904.6416796854, 135350.366810770]
 
    # Calculate delta in dB
    # analog_mag_pre_cal = analog_mag_pre_cal.flatten() 
    analog_mag_pre_cal = analog_mag_pre_cal.flatten()
    # bad_val_thresh = np.average(analog_mag_pre_cal) - 3
    # bad_val_thresh = np.average(analog_mag_pre_cal) - 2.5

    bad_val_thresh = np.average(analog_mag_pre_cal) - 6
    for i in range(np.size(analog_mag_pre_cal)):
        if analog_mag_pre_cal[i] < bad_val_thresh:
            print("Bad Value: ", analog_mag_pre_cal[i])
            print("Element Number: ", i)
            print("Replacing with bad val threshold ", bad_val_thresh)
            analog_mag_pre_cal[i] = bad_val_thresh


    mag_min = np.min(analog_mag_pre_cal)
    mag_cal_diff = np.zeros(np.shape(analog_mag_pre_cal))

    for i in range(np.size(analog_mag_pre_cal)):
        if (analog_mag_pre_cal[i] - mag_min <= 0.25):
            mag_cal_diff[i] = 0
        else:
            mag_cal_diff[i] = analog_mag_pre_cal[i] - mag_min
    
    mag_cal_poly = np.zeros(np.shape(analog_mag_pre_cal))

    # Find correct gain code values based on which polynomial should be used
    # Adjust attenuators accordingly
    for i in range(np.size(analog_mag_pre_cal)):

        mag_cal_poly.flat[i] = np.round(np.polyval(poly_atten1, -1 * mag_cal_diff[i]))

    # set min and max clipping to 0 and 127, respectively
    mag_cal_poly = np.clip(mag_cal_poly, 0, 127)
    gain_codes_cal = mag_cal_poly

    atten = np.zeros(np.shape(analog_mag_pre_cal))
    return gain_codes_cal, atten, mag_cal_diff

def strip_to_last_two_digits(input_string):
    """
    Extract the last two digits from a string.
    """
    # Find all sequences of digits in the string
    all_numbers = re.findall(r'\d+', input_string)

    # Join them together and take the last two digits
    last_two_digits = ''.join(all_numbers)[-2:]
    
    return last_two_digits

def create_dict(new_keys, array):
    """
    Convert a flattened array (1x64) into 8x8 and create a dictionary 
    where each key from new_keys (8x8) maps to its corresponding 8-value row.
    """
    # Type Checker
    if not isinstance(new_keys, np.ndarray):
        raise TypeError("new_keys must be a numpy array")
    if not isinstance(array, np.ndarray):
        raise TypeError("array must be a numpy array")

    array_shape = np.shape(new_keys)
    key_flat = new_keys.transpose().flatten()
    array_flat = array.transpose().flatten()

    result_dict = {}

    # Reshape new_keys and array into 8x8
    reshaped_keys = key_flat.reshape(array_shape,order='F')
    reshaped_array = array_flat.reshape(array_shape,order='F')

    # Map each key in reshaped_keys to the corresponding row in reshaped_array

    for i in range(array_shape[0]):
        for j in range(array_shape[0]):
            result_dict[reshaped_keys[i][j]] = reshaped_array[i][j]
    print("Dictionary created successfully of size:", array_shape)
    return result_dict

def wrap_to_360(angle):
    """Wrap angle to the range [0, 360)."""
    return angle % 360

def ind2sub(array_shape, index):
    """Convert a linear index to row and column indices."""
    rows = index % array_shape[0]
    cols = index // array_shape[0]
    return rows, cols

####################################################################################################
#               RX signal-chain calibration functions for ADSY2301 System                          #
####################################################################################################

# Calculates dBFS spectrum for 12-bit signed ADC data
def calc_dbfs(data):
    # Calculates dBFS spectrum for 12-bit signed ADC data
    NumSamples = len(data)
    win = np.hamming(NumSamples)
    y = data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    
    # Avoid log(0)
    s_mag = np.abs(s_shift)
    s_mag[s_mag == 0] = 1e-12

    # Convert to dBFS
    s_dbfs = 20 * np.log10(s_mag / (2**11))  # 2^11 = 2048 (full scale peak for signed 12-bit)
    return s_dbfs

def find_phase_delay_sliding_ref(obj, adc, subarray_ref, adc_map, delay_phases):
    """
    Measures calibrated phase offsets for Stingray reference channels in units of degrees using sliding reference.
    """

    # Enable the Stingray reference channels and capture data
    enable_rx_channel(obj,subarray_ref)
    data = np.array(data_capture(adc))

    # Create a list to store the calibration values for each antenna
    # Initialize the first antenna's calibration value to 0
    cal_ant = []
    cal_ant.append(0)

    for i in range(len(data)-1):
        peak_sum = []
        for phase_delay in delay_phases:

            # Apply the phase delay to the first and second antennas
            first_ant = phase_delayer(data[adc_map[i]], phase_delay*i+cal_ant[i])
            second_ant = phase_delayer(data[adc_map[i+1]], phase_delay*(i+1))

            # Calculate the delayed sum of the two antennas
            # and find the maximum value
            delayed_sum = calc_dbfs(first_ant - second_ant)
            peak_sum.append(np.max(delayed_sum))

        # Find the minimum value in the peak sum and its index
        # This index corresponds to the phase delay that minimizes the difference
        null_val = np.min(peak_sum)
        null_index = np.where(peak_sum==null_val)

    # Disable the Stingray reference channels
    disable_rx_channel(obj,subarray_ref)
    return cal_ant

def find_phase_delay_fixed_ref(obj, adc, subarray_ref, adc_ref, delay_phases):
    """
    Measures calibrated phase offsets for Stingray reference channels in units of degrees using fixed reference.
    """
    # Enable the Stingray reference channels and capture data
    enable_rx_channel(obj,subarray_ref)
    data = np.array(data_capture(adc))

    # Create a list to store the calibration values for each antenna
    # Initialize the first antenna's calibration value to 0
    cal_ant = []
    cal_ant.append(0)

    # Apply a zero phase delay to the reference antenna
    first_ant = phase_delayer(data[adc_ref], cal_ant[0])

    for i in range(len(data)):
        peak_sum = []
        for phase_delay in delay_phases:

            # Apply the phase delay second antennas
            second_ant = phase_delayer(data[i], phase_delay)

            # Calculate the delayed sum of the two antennas
            delayed_sum = calc_dbfs(first_ant - second_ant)

            # Find the maximum value
            peak_sum.append(np.max(delayed_sum))
        
        # Find the minimum value in the peak sum and its index
        null_val = np.min(peak_sum)
        null_index = np.where(np.abs(peak_sum)==np.abs(null_val))

        # Get the phase delay value that corresponds to the minimum peak sum
        # and append it to the calibration values list
        cal_value = delay_phases[null_index]
        cal_ant.append(cal_value[0].item())

    # Disable the Stingray reference channels
    disable_rx_channel(obj,subarray_ref)
    cal_ant = cal_ant[1:]
    # Roll the calibration values to align with the reference antenna
    # This is done because data[adc_ref] corresponds to subarray 4
    #return np.roll(cal_ant, -1)
    return cal_ant

def find_phase_delay_fixed_ref_tx(obj, SpecAn, subarray_ref, adc_ref, delay_phases):
    """
    Measures calibrated phase offsets for Stingray reference channels in units of degrees using fixed reference.
    """
    import adsy2301 as mr
    import paramiko
    import time

    # Enable the Stingray reference channels and capture data
    print("Setting PA_ON to 1")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
    time.sleep(1)
    ssh.close()

    mr.enable_tx_channel(obj, subarray_ref)
    # enable_rx_channel(obj,subarray_ref)
    # data = np.array(data_capture(adc))
    data = np.array(SpecAn.iq_complex_data())

    # Create a list to store the calibration values for each antenna
    # Initialize the first antenna's calibration value to 0
    cal_ant = []
    cal_ant.append(0)

    # Apply a zero phase delay to the reference antenna
    first_ant = phase_delayer(data[adc_ref], cal_ant[0])

    for i in range(len(data)):
        peak_sum = []
        for phase_delay in delay_phases:

            # Apply the phase delay second antennas
            second_ant = phase_delayer(data[i], phase_delay)

            # Calculate the delayed sum of the two antennas
            delayed_sum = calc_dbfs(first_ant - second_ant)

            # Find the maximum value
            peak_sum.append(np.max(delayed_sum))
        
        # Find the minimum value in the peak sum and its index
        null_val = np.min(peak_sum)
        null_index = np.where(np.abs(peak_sum)==np.abs(null_val))

        # Get the phase delay value that corresponds to the minimum peak sum
        # and append it to the calibration values list
        cal_value = delay_phases[null_index]
        cal_ant.append(cal_value[0].item())

    # Disable the Stingray reference channels
    disable_rx_channel(obj,subarray_ref)
    cal_ant = cal_ant[1:]
    # Roll the calibration values to align with the reference antenna
    # This is done because data[adc_ref] corresponds to subarray 4
    #return np.roll(cal_ant, -1)
    return cal_ant

def phase_digital(obj, adc, adc_ref, subarray_ref):
    """
    Measures calibrated phase offsets for AD9081 in units of milli-degrees.
    Returns digital phase offsets in a 1x4 row vector
    """
    # Enable analog array_reference channels for NCO calibration
    enable_rx_channel(obj, subarray_ref)

    # Capture ADC data
    data = np.array(data_capture(adc))

    # Extract sample 100 from each IQ, phase in degrees
    phase_compare = np.angle(data[:, 100], deg = True)

    # Measure phase delta with respect to reference and scale to millidegrees
    digital_phase_cal = (np.mod(phase_compare - phase_compare[adc_ref] + 180, 360) - 180) * 1e3

    # Disable analog array_reference channels
    disable_rx_channel(obj, subarray_ref)

    # write NCO phases to AD9081
    adc.rx_main_nco_phases = (np.round(digital_phase_cal).astype(int)).tolist()
 
    return digital_phase_cal

def get_gain_codes(obj,adc,subarray,adc_map, gain_dict, atten_dict):
    """
    Applies pre-calculated gain and attenuation values to Stingray elements.
    gain_dict and atten_dict should be passed from rx_gain function.
    """
    for element in obj.elements.values():
        """
        Iterate through each element in the Stingray object
        Convert the element to a string and extract the last two digits
        This is used to map the element to its corresponding gain and attenuation values
        in the dictionaries created above
        """

        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))
        if value in subarray:
            value = int(strip_to_last_two_digits(str_channel))

            element.rx_attenuator = atten_dict[value]
            element.rx_gain = gain_dict[value]

            obj.latch_rx_settings() # Latch SPI settings to devices

## Original cal to minimum amplitude ##
def rx_gain(obj, adc, subarray, adc_map, element_map):
    """
    Measures analog magnitude for Stingray to equalize amplitudes across all elements.
    Returns calibrated gain codes and magnitude in dBFS pre-calibration in an 8x8 matrix mapped to the Stingray elements.
    """
    
    # Capture ADC data with initial gain, attenuation, and phase settings
    data = rx_single_channel_data(obj, adc, subarray, adc_map)

    # Measure analog magnitude pre-calibration
    analog_mag_pre_cal = get_analog_mag(data)
    # Reshape the analog magnitude to match the subarray shape in column-major order
    # This is necessary to match the element_map mapping
    # analog_mag_pre_cal0 = np.reshape(analog_mag_pre_cal, np.shape(element_map), order = 'F')
    # Calculate gain codes and attenuation values based on pre-calibration magnitude
    gain_codes_cal, atten_cal, mag_cal_diff = gain_codes(obj, analog_mag_pre_cal, "rx")
    print(gain_codes_cal)
    # Create dictionary to assign gain codes and attenuation values to elements
    gain_dict = create_dict(element_map, gain_codes_cal)
    print("gain_dict:", gain_dict)
    atten_dict = create_dict(element_map, atten_cal)
    # print("atten_dict:", atten_dict)

    for element in obj.elements.values():
        """
        Iterate through each element in the Stingray object
        Convert the element to a string and extract the last two digits
        This is used to map the element to its corresponding gain and attenuation values
        in the dictionaries created above
        """
        str_channel = str(element)
        
        value = int(strip_to_last_two_digits(str_channel))

        element.rx_attenuator = atten_dict[value]
        element.rx_gain = gain_dict[value]

        obj.latch_rx_settings() # Latch SPI settings to devices
   
    # Capture ADC data with calibrated gain codes and attenuation values
    data = rx_single_channel_data(obj, adc, subarray, adc_map)
   
    # Measure analog magnitude post-calibration
    analog_mag_post_cal = get_analog_mag(data)

    print("PreCal Data:", analog_mag_pre_cal)
    print("PostCal Data:", analog_mag_post_cal)
 
    return gain_codes_cal, atten_cal, analog_mag_pre_cal, analog_mag_post_cal

def phase_analog(sray_obj, adc_obj, adc_map, adc_ref, subarray_ref, subarray_targ, dig_phase):
    """Calculate analog phase for each element in the subarray."""
    analog_phase = np.zeros((4, 16))  # Initialize phase array
    element_map = np.array([
        [1, 9,  17, 25, 33, 41, 49, 57],
        [2, 10, 18, 26, 34, 42, 50, 58],
        [3, 11, 19, 27, 35, 43, 51, 59],
        [4, 12, 20, 28, 36, 44, 52, 60],
 
        [5, 13, 21, 29, 37, 45, 53, 61],
        [6, 14, 22, 30, 38, 46, 54, 62],
        [7, 15, 23, 31, 39, 47, 55, 63],
        [8, 16, 24, 32, 40, 48, 56, 64]
        ])
    # break out subarray 1 cal, vs subarrays 2,3,4 cal
    for ii in range(2): 
        for jj in range(subarray_targ.shape[1]):
            dummy_array = np.zeros((4, 16))

            if ii == 0:

                # When calibrating subarray 1, use the reference channel from subarray 2
                tmp_array_ref = subarray_ref[1]

                # Assign the target channels from subarray 1 to tmp_targ
                tmp_targ = subarray_targ[0, :]

                # Enable the reference channel in subarray 2
                enable_rx_channel(sray_obj, tmp_array_ref)

                # Iterate through subarray 1 and enable one channel at a time (excludes the reference channel)
                enable_rx_channel(sray_obj, tmp_targ[jj])

                # Grab row and column indices for specific channel in subarray 1
                row, col = ind2sub(dummy_array.shape, tmp_targ[jj] - 1)

            else:

                # When calibrating subarrays 2, 3, and 4, use the reference channel from subarray 1
                tmp_array_ref = subarray_ref[0]

                # Assign the target channels from subarray 2, 3, and 4 to tmp_targ
                tmp_targ = subarray_targ[1:4]

                # Enable the reference channel in subarray 1
                enable_rx_channel(sray_obj, tmp_array_ref)

                # Enable the target channels in subarray 2, 3, and 4
                enable_rx_channel(sray_obj, tmp_targ[:, jj])

                # Grab row and column indices for specfic channel in subarray 2, 3, and 4
                row, col = ind2sub(dummy_array.shape, tmp_targ[:, jj] - 1)

            # Capture ADC data for the enabled channels
            data = data_capture_cal(adc_obj, dig_phase)
            data = np.array(data).T

            # Extract the phase information from the captured data and convert to degrees
            phase_compare = np.angle(data[100, :]) * 180 / np.pi

            if ii == 0:
                # When calibrating subarray 1, use the reference channel from subarray 2
                # analog_phase[row, col] = wrap_to_360(...) — original per-element assignment
                analog_phase[0, jj+1] = wrap_to_360(phase_compare[adc_map[0]] - phase_compare[adc_map[1]])
            else:
                for n in range(1, len(adc_map)):
                    analog_phase[n, jj+1] = wrap_to_360(phase_compare[adc_map[n]] - phase_compare[adc_ref])

            if ii == 0:
                # Disable the target channel in subarray 1
                disable_rx_channel(sray_obj, tmp_targ[jj])
            else:
                # Disable the target channels in subarrays 2, 3, and 4
                disable_rx_channel(sray_obj, tmp_targ[:, jj])

        # Disable the reference channel being used for calibration
        disable_rx_channel(sray_obj, tmp_array_ref)
                      
    analog_phase_flatten = np.concatenate((analog_phase[0,0:4], analog_phase[3,0:4], analog_phase[0,4:8], analog_phase[3,4:8], analog_phase[0,8:12], analog_phase[3,8:12], analog_phase[0,12:16], analog_phase[3,12:16], analog_phase[1,0:4], analog_phase[2,0:4], analog_phase[1,4:8], analog_phase[2,4:8], analog_phase[1,8:12], analog_phase[2,8:12], analog_phase[1,12:16], analog_phase[2,12:16]))
    analog_phase_dict = create_dict(element_map,analog_phase_flatten)
    

    for element in sray_obj.elements.values():
        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))

        # Assign the calculated phase to the element
        element.rx_phase = analog_phase_dict[value]
        sray_obj.latch_rx_settings()  # Latch SPI settings to devices

    return analog_phase_flatten, analog_phase_dict

def phase_analog_tx(adsy2301_obj, SpecAn_obj, adc_map, adc_ref, subarray_ref, subarray_targ, dig_phase):
    """Calculate analog phase for each element in the subarray."""

    import adsy2301 as mr

    analog_phase = np.zeros((4, 16))  # Initialize phase array
    element_map = np.array([
        [1, 9,  17, 25, 33, 41, 49, 57],
        [2, 10, 18, 26, 34, 42, 50, 58],
        [3, 11, 19, 27, 35, 43, 51, 59],
        [4, 12, 20, 28, 36, 44, 52, 60],
 
        [5, 13, 21, 29, 37, 45, 53, 61],
        [6, 14, 22, 30, 38, 46, 54, 62],
        [7, 15, 23, 31, 39, 47, 55, 63],
        [8, 16, 24, 32, 40, 48, 56, 64]
        ])
    # break out subarray 1 cal, vs subarrays 2,3,4 cal
    for ii in range(2): 
        for jj in range(subarray_targ.shape[1]):
            dummy_array = np.zeros((4, 16))

            if ii == 0:

                # When calibrating subarray 1, use the reference channel from subarray 2
                tmp_array_ref = subarray_ref[1]

                # Assign the target channels from subarray 1 to tmp_targ
                tmp_targ = subarray_targ[0, :]

                # Enable the reference channel in subarray 2
                mr.enable_tx_channel(adsy2301_obj, tmp_array_ref)
                # enable_rx_channel(sray_obj, tmp_array_ref)

                # Iterate through subarray 1 and enable one channel at a time (excludes the reference channel)
                mr.enable_tx_channel(adsy2301_obj, tmp_targ[jj])
                # enable_rx_channel(sray_obj, tmp_targ[jj])

                # Grab row and column indices for specific channel in subarray 1
                row, col = ind2sub(dummy_array.shape, tmp_targ[jj] - 1)

            else:

                # When calibrating subarrays 2, 3, and 4, use the reference channel from subarray 1
                tmp_array_ref = subarray_ref[0]

                # Assign the target channels from subarray 2, 3, and 4 to tmp_targ
                tmp_targ = subarray_targ[1:4]

                # Enable the reference channel in subarray 1
                mr.enable_tx_channel(adsy2301_obj, tmp_array_ref)
                # enable_rx_channel(sray_obj, tmp_array_ref)

                # Enable the target channels in subarray 2, 3, and 4
                mr.enable_tx_channel(adsy2301_obj, tmp_targ[:, jj])
                # enable_rx_channel(sray_obj, tmp_targ[:, jj])

                # Grab row and column indices for specfic channel in subarray 2, 3, and 4
                row, col = ind2sub(dummy_array.shape, tmp_targ[:, jj] - 1)

            # Capture SpecAn data for the enabled channels
            for i in range(2):
                ## Take Data from Spec An ##
                data = SpecAn_obj.iq_complex_data()
            data = cal_data(data, dig_phase) # only do phase delay cals, no gain    
            data = np.array(data).T

            # Extract the phase information from the captured data and convert to degrees
            phase_compare = np.angle(data[100, :]) * 180 / np.pi

            if ii == 0:
                analog_phase[0, jj+1] = wrap_to_360(phase_compare[adc_map[0]] - phase_compare[adc_map[1]])
            else:
                for n in range(1, len(adc_map)):
                    analog_phase[n, jj+1] = wrap_to_360(phase_compare[adc_map[n]] - phase_compare[adc_ref])

            if ii == 0:
                # Disable the target channel in subarray 1
                mr.disable_rx_channel(adsy2301_obj, tmp_targ[jj])
            else:
                # Disable the target channels in subarrays 2, 3, and 4
                mr.disable_rx_channel(adsy2301_obj, tmp_targ[:, jj])

        # Disable the reference channel being used for calibration
        mr.disable_rx_channel(adsy2301_obj, tmp_array_ref)
                      
    analog_phase_flatten = np.concatenate((analog_phase[0,0:4], analog_phase[3,0:4], analog_phase[0,4:8], analog_phase[3,4:8], analog_phase[0,8:12], analog_phase[3,8:12], analog_phase[0,12:16], analog_phase[3,12:16], analog_phase[1,0:4], analog_phase[2,0:4], analog_phase[1,4:8], analog_phase[2,4:8], analog_phase[1,8:12], analog_phase[2,8:12], analog_phase[1,12:16], analog_phase[2,12:16]))
    analog_phase_dict = create_dict(element_map,analog_phase_flatten)
    

    for element in adsy2301_obj.elements.values():
        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))

        # Assign the calculated phase to the element
        element.rx_phase = analog_phase_dict[value]
        adsy2301_obj.latch_rx_settings()  # Latch SPI settings to devices

    return analog_phase_flatten, analog_phase_dict

def rx_single_channel_data(obj, adc, array, adc_map):
        """
        Captures single channel Rx data on a 1 channel per subarray basis.
        Returns raw ADC codes in a 64x4096 matrix.
        """
        disable_rx_channel(obj,array)
        rx_data = np.zeros((np.size(array),4096), dtype = complex)  # Allocate memory
        for a in range(np.size(array,1)):
            
            # Enable one reference channel per subarray
            enable_rx_channel(obj, array[:,a])
            time.sleep(1)
            # Pull data from ADC
            data = np.array(data_capture(adc))
            data = data[:, :np.size(rx_data,1)] # remove data past 4096th column for FFT
            print(get_analog_mag(data))
            print(array[:,a])
            # Initialize temporary array for ADC data
            # This is used to map the ADC data to the correct subarray
            new_data = np.zeros(np.shape(data), dtype = complex)

            for i in range(len(adc_map)):
                # Map data to the correct ADC channels
                new_data[i,:] = data[adc_map[i],:]

          # Map the data to the correct row in the rx_data matrix
                # The row is determined by the index of the subarray
                # rx_data[i,:] = new_data[i,:]
            for index, row in enumerate(array[:,a]):

                # Map the data to the correct row in the rx_data matrix
                # The row is determined by the index of the subarray
                rx_data[row - 1,:] = new_data[index,:]

            # Disable target channels
            disable_rx_channel(obj, array[:,a])
        return rx_data
 
def get_analog_mag(data):
    """
    get_analog_mag runs an FFT on the data to create a matrix of magnitudes.
    Help: dataADC codes is a 32x4096 matrix of raw ADC codes.
    Returns analog_mag which is a 1x32 row vector of magnitudes in dBFS.
    """

   

    analog_mag = np.zeros((1, np.size(data,0)))
   
    if data.ndim == 1:
        adc_fft_data = fft(data, False, "OneTone")
        analog_mag = adc_fft_data["A:mag_dbfs"]
    else:
        for i in range(np.size(data,0)):
            adc_fft_data = fft(data[i,:], False, "OneTone")
            analog_mag[0,i] = adc_fft_data['A:mag_dbfs']
    
    
    return analog_mag
 
def fft(complex_data, combined_waveforms, tone_type):
    """
    FFT on ADC sample domain waveform data
    """
    qres = 16 # padding out 12 bit ADC to 16 for FFT algorithm
    qres_grow = 18 # bit growth needed to accomadate combining 4 FFTs
    navg = 1
    nfft = 4096
    # Check if bit padding needed
    if combined_waveforms == True:
        qres = qres_grow
        data = complex_data
    elif combined_waveforms == False:
        qres = qres
        data = complex_data
    else:
        raise ValueError('combined_waveforms type unsupported. True or False are acceptable types.')
   
    real_data = data.real.astype(np.int32)
    imag_data = data.imag.astype(np.int32)
    tone_type = tone_type.lower()
    if tone_type == "twotone" and os.path.exists("rx_2tone.json"):
        try:
            with open('rx_2tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    elif tone_type == "onetone" and os.path.exists("rx_1tone.json"):
        try:
            with open('rx_1tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    else:
        raise ValueError('tone_type type unsupported. OneTone or TwoTone are acceptable types.')
    
    # Fourier analysis configuration
    if file.name == "rx_1tone.json":
        key = "fa"
        gn.mgr_remove(key)
        gn.fa_create(key)
        gn.fa_load(file.name, key)
    else:
        raise AttributeError("Have not coded rx_2tone.json for genalyzer yet")
    
    # Do FFT analysis
    window = gn.Window.HANN # window function to apply
    code_fmt = gn.CodeFormat.TWOS_COMPLEMENT # integer data format
    axis_type = gn.FreqAxisType.DC_CENTER # axis type
   
    fft_complex = gn.fft(real_data, imag_data, qres, navg, nfft, window, code_fmt)
    fft_results = gn.fft_analysis(key, fft_complex, nfft, axis_type)

    results = fft_results

    return fft_results

def quantize_phase(phase, bits=8):
    """Quantize phase values to specified number of bits"""
    levels = 2**bits
    phase_max = 2*np.pi
    step = phase_max/levels
    return np.round(phase/step)*step

def calc_array_pattern(theta_sweep=(-90, 90), sweep_step=0.5,f_op_GHz=10, elec_steer_angle=[0], M=8, N=8):  # Electronic steering angles (az or el)

    # === Constants ===
    from scipy.constants import c
    lambda_op = c / (f_op_GHz * 1e9)      # Wavelength at 11 GHz
    k = 2 * np.pi / lambda_op             # Wavenumber
    d = 0.013635                            # Element spacing = 13.63 mm
    elec_steer_angle = -elec_steer_angle  # Convert to negative for correct direction
    # === Sweep settings
    # Quantized phase settings
    quantize_phased = quantize_phase(np.radians(theta_sweep), bits=8)
    theta_sweep = np.degrees(quantize_phased)

    mechanical_sweep = np.arange(theta_sweep[0], theta_sweep[1]+sweep_step, sweep_step)    # Mechanical sweep angles
    # elec_steer_angles = np.arange(-20, 21, 10)      # Electronic steering angles (az or el)

    # === Array size
    # M, N = 8, 8
    x = (np.arange(N) - (N - 1) / 2) * d  # X-coordinates (azimuth direction)
    y = (np.arange(M) - (M - 1) / 2) * d  # Y-coordinates (elevation direction)

    # === Initialize storage
    azim_results = []
    elev_results = []

    steer_rad = np.radians(elec_steer_angle)
    # Electronic steering along X-axis (azimuth)
    steering_weights = np.exp(1j * k * x * np.sin(steer_rad))
    response = []
    for mech_angle in mechanical_sweep:
        mech_rad = np.radians(mech_angle)
        incoming_phase = np.exp(1j * k * x * np.sin(mech_rad))
        pattern = np.dot(steering_weights, incoming_phase)
        response.append(np.abs(pattern))
    response = 20 * np.log10(np.clip(np.array(response) / np.max(response), 1e-10, None))
    azim_results.append(response)
    #Force Column Vector
    azim_results = np.array(azim_results).reshape(-1, 1)

    # === Elevation Beampattern Simulation
    steer_rad = np.radians(elec_steer_angle)
    # Electronic steering along Y-axis (elevation)
    steering_weights = np.exp(1j * k * y * np.sin(steer_rad))
    response = []
    for mech_angle in mechanical_sweep:
        mech_rad = np.radians(mech_angle)
        incoming_phase = np.exp(1j * k * y * np.sin(mech_rad))
        pattern = np.dot(steering_weights, incoming_phase)
        response.append(np.abs(pattern))
    response = 20 * np.log10(np.clip(np.array(response) / np.max(response), 1e-10, None))
    elev_results.append(response)
    #Force Column Vector
    elev_results = np.array(elev_results).reshape(-1, 1)
    elec_steer_angle = -elec_steer_angle  # Convert back to positive for output
    
    return mechanical_sweep, elec_steer_angle, azim_results, elev_results,  # Return the mechanical sweep angles and the pattern for the boresight angle

def change_duty_cycle(talise_uri, PRI_ms, off_ms):

    tddn = adi.tddn(talise_uri)
    tddn.frame_length_ms      = PRI_ms
    tddn.enable = 0
    tddn.sync_soft  = 0
    TDD_CHANNEL7     = 7  ## TR Pulse
    for chan in [TDD_CHANNEL7]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = off_ms  # for example off_ms = 0.005 would make a 5% duty cycle when the PRI_ms = 0.1
        tddn.channel[chan].polarity = 0
        tddn.channel[chan].enable   = 1
    tddn.enable = 1
    tddn.sync_soft  = 1
    
def sdr_init(dev):

    # Configure TX/RX hardware gains (0 dB)
    dev.ADRV9009.tx_enabled_channels = [0, 1, 2, 3]
    dev.ADRV9009.rx_enabled_channels = [0, 1, 2, 3]
    print("TX channels enabled ", dev.ADRV9009.tx_enabled_channels)
    print("RX channels enabled ", dev.ADRV9009.rx_enabled_channels)

    dev.ADRV9009.trx_lo = 4500000000
    print("Side A TRX LO frequency set to ", dev.ADRV9009.trx_lo)

    dev.ADRV9009.trx_lo_chip_b = 4500000000
    print("Side B TRX LO frequency set to ", dev.ADRV9009.trx_lo_chip_b)

    dev.ADRV9009.tx_hardwaregain_chan0 = -14
    dev.ADRV9009.tx_hardwaregain_chan1 = -14
    dev.ADRV9009.tx_hardwaregain_chan0_chip_b= -14
    dev.ADRV9009.tx_hardwaregain_chan1_chip_b = -14
    print("Side A TX hardware gain for channel 0 set to ", dev.ADRV9009.tx_hardwaregain_chan0)
    print("Side A TX hardware gain for channel 1 set to ", dev.ADRV9009.tx_hardwaregain_chan1)
    print("Side B TX hardware gain for channel 0 set to ", dev.ADRV9009.tx_hardwaregain_chan0_chip_b)
    print("Side B TX hardware gain for channel 1 set to ", dev.ADRV9009.tx_hardwaregain_chan1_chip_b)

    dev.ADRV9009.rx_hardwaregain_chan0 = 0
    dev.ADRV9009.rx_hardwaregain_chan1 = 0
    dev.ADRV9009.rx_hardwaregain_chan0_chip_b= 0
    dev.ADRV9009.rx_hardwaregain_chan1_chip_b = 0
    print("Side A RX hardware gain for channel 0 set to ", dev.ADRV9009.rx_hardwaregain_chan0)
    print("Side A RX hardware gain for channel 1 set to ", dev.ADRV9009.rx_hardwaregain_chan1)
    print("Side B RX hardware gain for channel 0 set to ", dev.ADRV9009.rx_hardwaregain_chan0_chip_b)
    print("Side B RX hardware gain for channel 1 set to ", dev.ADRV9009.rx_hardwaregain_chan1_chip_b)

    dev.ADRV9009.gain_control_mode_chan0 = "manual"
    dev.ADRV9009.gain_control_mode_chan1 = "manual"
    dev.ADRV9009.gain_control_mode_chan0_chip_b = "manual"
    dev.ADRV9009.gain_control_mode_chan1_chip_b = "manual"
    print("Side A Gain control mode for channel 0 set to ", dev.ADRV9009.gain_control_mode_chan0)
    print("Side A Gain control mode for channel 1 set to ", dev.ADRV9009.gain_control_mode_chan1)
    print("Side B Gain control mode for channel 0 set to ", dev.ADRV9009.gain_control_mode_chan0_chip_b)
    print("Side B Gain control mode for channel 1 set to ", dev.ADRV9009.gain_control_mode_chan1_chip_b)

    dev.ADRV9009._rxadc.set_kernel_buffers_count(1)
    dev.ADRV9009.rx_enabled_channels = [0, 1, 2, 3]
    dev.ADRV9009.rx_buffer_size = 2 ** 12  # 4096 samples per capture
    dev.ADRV9009.dds_phases = []
    print("Sample Rate RX Channels: %.2fMSPS" %(dev.ADRV9009.rx_sample_rate_chip_b/1e6))

    print("SDR initialized.")

def tdd_init(dev,TXRX_Bit):

    DAC = False
    tddn = adi.tddn(dev.uri)

    ## Pulse Parameters ##
    PRI_ms = 0.1 # Pulse repetition interval (ms)
    frame_length_ms = 0.1    # 100 us frame
    DAC_duty_cycle = 1.0   # Duty cycle for DAC pulses (0.0 to 1.0)
    frame_pulses_to_plot = 5  # (will be used to calculate the RX buffer size)

    ###########################
    # TDD Engine Configuration: Name and TDD channel 
    ###########################

    TDD_TX_OFFLOAD_SYNC = 0
    TDD_RX_OFFLOAD_SYNC = 1
    TDD_ENABLE      = 2
    TDD_ADRV9009_RX_EN = 3
    TDD_ADRV9009_TX_EN = 4
    # TDD_ADSY2301_EN = 5
    TDD_PA_ON     = 6  # PA_ON_0, PA_ON_1, PA_ON_2, PA_ON_3
    TDD_TR_PULSE     = 7  # TR Pulse
    TDD_RX_LOAD = 12
    TDD_TX_LOAD = 13

    # Configure TDD engine (disable during changes)
    tddn.enable = False
    tddn.frame_length_ms = frame_length_ms  # frame_length_ms = PRI_ms

    # --- Group 1: Always-on channels ---
    for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN, TDD_PA_ON]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = frame_length_ms
        tddn.channel[chan].polarity = 0
        tddn.channel[chan].enable   = True

    # --- Group 2: TX/RX offload sync (raw sample counts) ---
    for chan in [TDD_TX_OFFLOAD_SYNC,TDD_RX_OFFLOAD_SYNC]:
        tddn.channel[chan].on_raw   = 0
        tddn.channel[chan].off_raw  = 10 
        tddn.channel[chan].polarity = 0
        tddn.channel[chan].enable   = True

    # --- Group 3: TR pulse ---
    for chan in [TDD_TR_PULSE]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0.005  # 5 us TR pulse (5% duty cycle at 100 us PRI)
        tddn.channel[chan].polarity = 0      # polarity inverted
        tddn.channel[chan].enable   = True

    # --- Enable TDD engine and trigger sync ---
    tddn.enable = True
    tddn.sync_soft  = True

    if DAC:

        pulse_spacing_ms = 0.002        # 2 us spacing between pulse start times
        pulse_start_buffer_ms = 0.00001 # 10 ns guard
        pulse0_start_ms = pulse_start_buffer_ms
        pulse0_stop_ms = DAC_duty_cycle * PRI_ms + pulse_start_buffer_ms
        pulse1_start_ms = pulse0_stop_ms + pulse_spacing_ms
        pulse1_stop_ms = pulse1_start_ms + DAC_duty_cycle * PRI_ms
        pulse2_start_ms = pulse1_stop_ms + pulse_spacing_ms
        pulse2_stop_ms = pulse2_start_ms + DAC_duty_cycle * PRI_ms
        pulse3_start_ms = pulse2_stop_ms + pulse_spacing_ms
        pulse3_stop_ms = pulse3_start_ms + DAC_duty_cycle * PRI_ms

        # Prepare TX data
        fs = int(dev.ADRV9009.tx_sample_rate)
        frame_length_seconds = PRI_ms * 1e-3
        # TX carrier frequency (Hz)
        fc = 1000e3
        # calculate N for full frame duration: N = fs * frame_length_seconds
        N = int(fs * frame_length_seconds)
        ts = 1 / float(fs)
        frame_length_ms = PRI_ms

        #######################
        ## Setup DAC outputs ##
        #######################
        # Calculate samples for TX pulse duration
        pulse0_duration_ms = pulse0_stop_ms - pulse0_start_ms
        pulse0_duration_seconds = pulse0_duration_ms * 1e-3
        pulse0_samples = int(fs * pulse0_duration_seconds)
        pulse0_start_sample = int(fs * pulse0_start_ms * 1e-3)

        pulse1_duration_ms = pulse1_stop_ms - pulse1_start_ms
        pulse1_duration_seconds = pulse1_duration_ms * 1e-3
        pulse1_samples = int(fs * pulse1_duration_seconds)
        pulse1_start_sample = int(fs * pulse1_start_ms * 1e-3)

        pulse2_duration_ms = pulse2_stop_ms - pulse2_start_ms
        pulse2_duration_seconds = pulse2_duration_ms * 1e-3
        pulse2_samples = int(fs * pulse2_duration_seconds)
        pulse2_start_sample = int(fs * pulse2_start_ms * 1e-3)

        pulse3_duration_ms = pulse3_stop_ms - pulse3_start_ms
        pulse3_duration_seconds = pulse3_duration_ms * 1e-3
        pulse3_samples = int(fs * pulse3_duration_seconds)
        pulse3_start_sample = int(fs * pulse3_start_ms * 1e-3)

        # Create full frame with zeros
        pulse0_i = np.zeros(N)
        pulse0_q = np.zeros(N)
        pulse1_i = np.zeros(N)
        pulse1_q = np.zeros(N)
        pulse2_i = np.zeros(N)
        pulse2_q = np.zeros(N)
        pulse3_i = np.zeros(N)
        pulse3_q = np.zeros(N)

        for n in range(pulse0_start_sample, min(pulse0_start_sample + pulse0_samples, N)):
            t_sample = n * ts
            pulse0_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
            pulse0_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
        for n in range(pulse1_start_sample, min(pulse1_start_sample + pulse1_samples, N)):
            t_sample = n * ts
            pulse1_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
            pulse1_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
        for n in range(pulse2_start_sample, min(pulse2_start_sample + pulse2_samples, N)):
            t_sample = n * ts
            pulse2_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
            pulse2_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
        for n in range(pulse3_start_sample, min(pulse3_start_sample + pulse3_samples, N)):
            t_sample = n * ts
            pulse3_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
            pulse3_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

        pulse0_data = pulse0_i + 1j * pulse0_q
        pulse1_data = pulse1_i + 1j * pulse1_q
        pulse2_data = pulse2_i + 1j * pulse2_q
        pulse3_data = pulse3_i + 1j * pulse3_q

        dev.ADRV9009.tx_destroy_buffer()

        # scaling for 16-bit DAC
        # use most of the dynamic range but avoid clipping
        scale_factor = 2**15 - 1
        pulse0_iq_real = np.int16(np.real(pulse0_data) * scale_factor)
        pulse0_iq_imag = np.int16(np.imag(pulse0_data) * scale_factor)
        pulse0_iq = pulse0_iq_real + 1j * pulse0_iq_imag

        pulse1_iq_real = np.int16(np.real(pulse1_data) * scale_factor)
        pulse1_iq_imag = np.int16(np.imag(pulse1_data) * scale_factor)
        pulse1_iq = pulse1_iq_real + 1j * pulse1_iq_imag

        pulse2_iq_real = np.int16(np.real(pulse2_data) * scale_factor)
        pulse2_iq_imag = np.int16(np.imag(pulse2_data) * scale_factor)
        pulse2_iq = pulse2_iq_real + 1j * pulse2_iq_imag

        pulse3_iq_real = np.int16(np.real(pulse3_data) * scale_factor)
        pulse3_iq_imag = np.int16(np.imag(pulse3_data) * scale_factor)
        pulse3_iq = pulse3_iq_real + 1j * pulse3_iq_imag

        # Configure TX data offload mode to cyclic
        dev.ADRV9009._txdac.debug_attrs["pl_ddr_fifo_enable"].value = "1"
        dev.ADRV9009.tx_cyclic_buffer = True

        # Calculate RX buffer size to match TX duration
        rx_fs = int(dev.ADRV9009.rx_sample_rate)

        # Match RX buffer duration to TX duration
        desired_rx_duration = frame_pulses_to_plot * len(pulse0_iq) / fs * 1000  # ms
        rx_buffer_samples = int(rx_fs * (desired_rx_duration * 1e-3))
        dev.ADRV9009.rx_buffer_size = rx_buffer_samples

        ##############################################
        ## Step 3: Send TX Data
        ##############################################

        dev.ADRV9009.tx_destroy_buffer()

        if TXRX_Bit == 1:
            dev.ADRV9009.tx_enabled_channels = [0, 1, 2, 3]
            dev.ADRV9009.tx([pulse0_iq, pulse0_iq, pulse0_iq, pulse0_iq])
    
        if TXRX_Bit == 0:
            dev.ADRV9009.tx_enabled_channels = []
            dev.ADRV9009.tx([])

        dev.ADRV9009.tx_cyclic_buffer = True

        # Trigger TDD synchronization
        tddn.sync_soft  = True
        print("TDD Engine Started")

