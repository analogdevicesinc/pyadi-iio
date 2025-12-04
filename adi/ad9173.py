# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from adi.attribute import attribute
from adi.context_manager import context_manager
import math
import numpy as np
from random import randrange

# out_altvoltage0_channel_nco_enable
# out_altvoltage0_channel_nco_frequency
# out_altvoltage0_channel_nco_phase
# out_altvoltage0_channel_nco_scale
# out_altvoltage0_main_nco_enable
# out_altvoltage0_main_nco_frequency
# out_altvoltage0_main_nco_phase

class ad9173(attribute, context_manager):
    """AD9173 Microwave Wideband Synthesizer
    with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with AD9173
        dac_frequency: type=float
            DAC clock frequency in Hz
    """

    _device_name = "ad9173"

    SPI_PAGEINDX_REG = 0x8
    SCRATCHPAD_REG = 0xA
    FSC0_REG = 0x59
    FSC1_REG = 0x5a
    INIT_FILE_READ_DUMMY = 0xFF
    DDSM_DATAPATH_CFG_REG = 0x112
    DDSM_FTW_UPDATE_REG = 0x113
    DDSM_FTW0_REG = 0x114
    DDSM_FTW5_REG = 0x119
    DDSC_FTW_UPDATE_REG = 0x131
    DDSC_FTW0_REG = 0x132
    DC_CAL_TONE_LSB_REG = 0x148
    DC_CAL_TONE_MSB_REG = 0x149
    BLANKING_CTRL_REG = 0x596

    FTW_WIDTH = 48
    FTW_BYTES = 6
    FSC_MIN = 16
    FSC_RANGE = 25
    DCTONE_FULL_SCALE = 0x50ff
    DEFAULT_DAC_CLK = 488281.25 * 9

    def __init__(self, uri="", dac_frequency=12e9):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("AD9173 device not found")

        self._dac_frequency = dac_frequency #TODO: Controlled in Python for now, need to add to device tree
        self._df = int((2 ** self.FTW_WIDTH) * self.DEFAULT_DAC_CLK / self._dac_frequency)

    @property
    def channel0_nco_enable(self):
        """Get/Set the enable of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_enable", True, self._ctrl)

    @channel0_nco_enable.setter
    def channel0_nco_enable(self, value):
        """Get/Set the enable of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_enable", True, value, self._ctrl)

    @property
    def channel0_nco_frequency(self):
        """Get/Set the frequency of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_frequency", True, self._ctrl)

    @channel0_nco_frequency.setter
    def channel0_nco_frequency(self, value):
        """Get/Set the frequency of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_frequency", True, value, self._ctrl)

    @property
    def channel0_nco_scale(self):
        """Get/Set the scale of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_scale", True, self._ctrl)

    @channel0_nco_scale.setter
    def channel0_nco_scale(self, value):
        """Get/Set the scale of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_scale", True, value, self._ctrl)

    @property
    def main0_nco_frequency(self):
        """Get/Set the frequency of the main0 NCO"""
        return self._get_iio_attr("altvoltage0", "main_nco_frequency", True, self._ctrl)

    @main0_nco_frequency.setter
    def main0_nco_frequency(self, value):
        """Get/Set the frequency of the main0 NCO"""
        self._set_iio_attr("altvoltage0", "main_nco_frequency", True, value, self._ctrl)

    @property
    def channel1_nco_enable(self):
        """Get/Set the enable of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_enable", True, self._ctrl)

    @channel1_nco_enable.setter
    def channel1_nco_enable(self, value):
        """Get/Set the enable of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_enable", True, value, self._ctrl)

    @property
    def channel1_nco_frequency(self):
        """Get/Set the frequency of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_frequency", True, self._ctrl)

    @channel1_nco_frequency.setter
    def channel1_nco_frequency(self, value):
        """Get/Set the frequency of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_frequency", True, value, self._ctrl)

    @property
    def channel1_nco_scale(self):
        """Get/Set the scale of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_scale", True, self._ctrl)

    @channel1_nco_scale.setter
    def channel1_nco_scale(self, value):
        """Get/Set the scale of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_scale", True, value, self._ctrl)

    @property
    def main1_nco_frequency(self):
        """Get/Set the frequency of the main1 NCO"""
        return self._get_iio_attr("altvoltage1", "main_nco_frequency", True, self._ctrl)

    @main1_nco_frequency.setter
    def main1_nco_frequency(self, value):
        """Get/Set the frequency of the main1 NCO"""
        self._set_iio_attr("altvoltage1", "main_nco_frequency", True, value, self._ctrl)

    @property
    def modulation_switch_mode(self):
        """Get/Set the Modulation switch mode"""
        return self._get_iio_attr("altvoltage0", "modulation_switch", True, self._ctrl)

    @modulation_switch_mode.setter
    def modulation_switch_mode(self, value):
        """Get/Set the Modulation switch mode"""
        self._set_iio_attr("altvoltage0", "modulation_switch", True, value, self._ctrl)

    def reg_write_multiple(self, reg, len, value):
        """Direct Register Access via debugfs write multiple"""
        self._set_iio_debug_attr_str("reg_write_mult", f"{reg} {len} {value}", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return int(self._get_iio_debug_attr_str("direct_reg_access", self._ctrl), 16)

    def write_bitfield(self, reg_addr, bit_msb, bit_lsb, val):
        """
        Write a value to a bitfield in a register.
        """
        bitlen = bit_msb - bit_lsb + 1

        regval = self.reg_read(reg_addr)
        bitmask = ((2 ** bitlen) - 1) << bit_lsb
        bf_val = regval & bitmask
        resi = regval - bf_val
        new_reg = resi + (val << bit_lsb)
        self.reg_write(reg_addr, new_reg)

    def read_bitfield(self, reg_addr, bit_msb, bit_lsb):
        """
        Read a value from a bitfield in a register.
        """
        bitlen = bit_msb - bit_lsb + 1
        regval = self.reg_read(reg_addr)
        bitmask = ((2 ** bitlen) - 1) << bit_lsb
        return (regval & bitmask) >> bit_lsb

    @property
    def dac_page(self):
        """Get current DAC Page setting"""
        val = (self.reg_read(self.SPI_PAGEINDX_REG) >> 6) & 0x03
        return val

    @dac_page.setter
    def dac_page(self,dac_mask):
        """Set current DAC Page setting"""
        self.reg_write(self.SPI_PAGEINDX_REG, (dac_mask << 6))

    @property
    def full_scale_current(self):
        """
        Get full-scale current for DAC(s).

        :return: Full scale current in mA
        """

        fsc0 = self.reg_read(self.FSC0_REG) & 0b11
        fsc1 = self.reg_read(self.FSC1_REG)
        code = (fsc1 << 2) + fsc0
        current_ma = (self.FSC_MIN + code * (self.FSC_RANGE / 1024))
        return current_ma

    @full_scale_current.setter
    def full_scale_current(self, current_ma):
        """
        Set full-scale current for DAC(s).
        :param current_ma: Desired full scale current in mA
        """
        code = int(math.floor(1024 * (current_ma - self.FSC_MIN) / self.FSC_RANGE))
        self.reg_write(self.FSC0_REG, code&0b11)
        self.reg_write(self.FSC1_REG, code>>2)

    @property
    def tx_enable(self):
        """
        Read enable status for DAC(s).
        :return: 0=disable, 1=enable
        """
        return self.read_bitfield(self.BLANKING_CTRL_REG, 3, 3)

    @tx_enable.setter
    def tx_enable(self, enable):
        """
        Enable or disable TX for DAC(s).
        :param enable: 0=disable, 1=enable
        """
        self.write_bitfield(self.BLANKING_CTRL_REG, 3, 3, enable)

    @property
    def dc_test_tone_amplitude(self):
        """
        Get DC test tone amplitude in dB for DAC(s).
        :return: Amplitude in dB
        """
        dc_msb = self.reg_read(self.DC_CAL_TONE_MSB_REG)
        dc_lsb = self.reg_read(self.DC_CAL_TONE_LSB_REG)
        return 20 * np.log10(float((dc_msb << 8) + dc_lsb) / self.DCTONE_FULL_SCALE)

    @dc_test_tone_amplitude.setter
    def dc_test_tone_amplitude(self, amplitude_db):
        """
        Set DC test tone amplitude of DAC(s).
        :param amplitude_db: Desired test tone amplitude in dB (should be <= 0)
        """
        if amplitude_db > 0:
            amplitude_db = 0
        dc_code = int(math.floor(self.DCTONE_FULL_SCALE * (10 ** (float(amplitude_db) / 20))))
        dc_lsb = dc_code & 0xFF
        dc_msb = (dc_code >> 8) & 0xFF
        self.reg_write(self.DC_CAL_TONE_MSB_REG, dc_msb)
        self.reg_write(self.DC_CAL_TONE_LSB_REG, dc_lsb)

    @property
    def dac_nco_frequency(self):
        """
        Get configured DAC frequency in Hz, using direct SPI reads
        :return: NCO Frequency in Hz
        """

        ftw = 0
        for x in range(self.FTW_BYTES):
            ftw = (ftw << 8) + self.reg_read(self.DDSM_FTW5_REG - x)
        val = (ftw * self._dac_frequency) / (2 ** self.FTW_WIDTH)

        return val

    @dac_nco_frequency.setter
    def dac_nco_frequency(self, freq_hz):
        """
        Set DAC frequency for selected DAC(s), using direct SPI writes
        :param freq_hz: Desired frequency in Hz
        """
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x0)
        ftw = int(round((2 ** self.FTW_WIDTH) * float(freq_hz) / float(self._dac_frequency)))
        for ix in range(self.FTW_BYTES):
            self.reg_write(self.DDSM_FTW0_REG + ix, (ftw >> (ix * 8)) & 0xFF)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x0)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x1)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x0)

    @property
    def dac_nco_ftw(self):
        """
        Get Programmed Frequency Tuning Word (FTW) for DAC(s), using direct SPI reads.
        :return: FTW value (int)
        """
        ftw = 0
        for x in range(self.FTW_BYTES):
            ftw = (ftw << 8) + self.reg_read(self.DDSM_FTW5_REG - x)
        return ftw

    @dac_nco_ftw.setter
    def dac_nco_ftw(self, ftw):
        """
        Set DAC FTW for slow sweep operation starting from the least significant byte, using direct SPI writes.
        :param ftw: Frequency Tuning Word (int)
        """
        for ix in range(self.FTW_BYTES):
            self.reg_write(self.DDSM_FTW0_REG + ix, (ftw >> (ix * 8)) & 0xFF)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x0)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x1)

    def set_dac_nco_ftw_reverse(self, ftw):
        """
        Set DAC FTW for slow sweep operation starting from the most significant byte.
        :param ftw: Frequency Tuning Word (int)
        """
        for ix in range(self.FTW_BYTES - 1, -1, -1):
            self.reg_write(self.DDSM_FTW0_REG + ix, (ftw >> (ix * 8)) & 0xFF)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x0)
        self.reg_write(self.DDSM_FTW_UPDATE_REG, 0x2)

    def set_relative_frequency(self, freq_hz):
        """
        Set DAC outputs to freq and freq+df
        :param freq_hz: Frequency in Hz
        """
        ftw = int(round((2 ** self.FTW_WIDTH) * float(freq_hz) / float(self._dac_frequency)))
        self.dac_page = 0x1
        self.dac_nco_ftw = ftw
        self.dac_page = 0x2
        self.dac_nco_ftw = ftw + self._df

    def zero_ddsc(self):
        """
        Zeroes out DDSC FTW registers
        """
        self.reg_write(self.SPI_PAGEINDX_REG, 0xff)
        self.reg_write(self.DDSC_FTW_UPDATE_REG, 0x0)
        for ix in range(self.FTW_BYTES):
            self.reg_write(self.DDSC_FTW0_REG + ix, 0)
        self.reg_write(self.DDSC_FTW_UPDATE_REG, 0x0)
        self.reg_write(self.DDSC_FTW_UPDATE_REG, 0x1)
        self.reg_write(self.DDSC_FTW_UPDATE_REG, 0x0)

    def enable_iq_output(self):
        """
        Enable IQ output mode.
        """
        self.reg_write(self.SPI_PAGEINDX_REG, 0x40)
        self.reg_write(self.INIT_FILE_READ_DUMMY, 0x1)
        self.reg_write(self.DDSM_DATAPATH_CFG_REG, 0x79)
        self.reg_write(self.SPI_PAGEINDX_REG, 0x80)
        self.reg_write(self.DDSM_DATAPATH_CFG_REG, 0x71)
        self.reg_write(self.BLANKING_CTRL_REG, 0xC)

    def self_test(self):
        """
        Perform SPI self-test by writing and reading scratchpad register.
        :return: 'Pass' or 'Fail'
        """
        is_fail = 'Pass'
        for _ in range(10):
            num = randrange(0xfe)
            self.reg_write(self.SCRATCHPAD_REG, num)
            ret = self.reg_read(self.SCRATCHPAD_REG)
            if num != ret:
                is_fail = 'Fail'
        return is_fail

    def program_init_file(self, init_file_path):
        """
        Initialize DAC with a series of register writes from given file and perform self-test.
        :param init_file_path: Filepath to text file of register writes
        """
        line_count = 0
        with open(init_file_path, "r") as fptr:
            for line in fptr:
                instr = line.split()
                self.reg_write(int(instr[0], 16), int(instr[1], 16))
                _ = self.reg_read(int(instr[0], 16)) # dummy read
                line_count += 1
        print(f'\n\t AD9173 Self Test Status: {self.self_test()}')