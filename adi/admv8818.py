# Copyright (C) 2021 Analog Devices, Inc.
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

from time import time
from adi.attribute import attribute
from adi.context_manager import context_manager


class admv8818(attribute, context_manager):
    """ADMV8818 2 GHz to 18 GHz, Digitally Tunable, High-Pass and Low-Pass Filter

    parameters:
        uri: type=string
            URI of IIO context with ADMV8818
    """

    _device_name = "admv8818"

    WR0_SW_REG = 0x20
    WR0_FILTER_REG = 0x21
    PRODUCT_ID_H_REG = 0x5

    WR0_SW_OUT_MASK = 0x07
    WR0_SW_IN_MASK = 0x07
    WR0_SW_IN_SHIFT = 3
    WR0_FILTER_LPF_MASK = 0x0F
    WR0_FILTER_HPF_MASK = 0x0F
    WR0_FILTER_HPF_SHIFT = 4
    WR0_SW_SET_VAL = 0x3
    WR0_SW_SET_SHIFT = 6

    PRODUCT_ID_H_VALUE = 0x88
    MAX_REG_ADDR = 0x200

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._device_name = device_name
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADMV8818 device not found")

    @property
    def low_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_low_pass_3db_frequency", True, self._ctrl
        )

    @low_pass_3db_frequency.setter
    def low_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0", "filter_low_pass_3db_frequency", True, int(value), self._ctrl
        )

    @property
    def high_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_high_pass_3db_frequency", True, self._ctrl
        )

    @high_pass_3db_frequency.setter
    def high_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_high_pass_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_bandwidth_3db_frequency(self):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_bandwidth_3db_frequency", True, self._ctrl
        )

    @band_pass_bandwidth_3db_frequency.setter
    def band_pass_bandwidth_3db_frequency(self, value):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_bandwidth_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_center_frequency(self):
        """Get/Set the Band Pass Center Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_center_frequency", True, self._ctrl
        )

    @band_pass_center_frequency.setter
    def band_pass_center_frequency(self, value):
        """Get/Set the Band Pass Center Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_center_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def mode_available(self):
        """Get available modes"""
        return self._get_iio_attr_str("altvoltage0", "mode_available", True, self._ctrl)

    @property
    def mode(self):
        """Get/Set mode"""
        return self._get_iio_attr_str("altvoltage0", "mode", True, self._ctrl)

    @mode.setter
    def mode(self, value):
        """Get/Set mode"""
        self._set_iio_attr("altvoltage0", "mode", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return int(self._get_iio_debug_attr_str("direct_reg_access", self._ctrl), 16)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    def write_bitfield(self, reg_addr, bit_msb, bit_lsb, val):
        """
        Write a value to a bitfield in a register.
        :param reg_addr: Register address
        :param bit_msb: Most significant bit
        :param bit_lsb: Least significant bit
        :param val: Value to write
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

        :param reg_addr: Register address
        :param bit_msb: Most significant bit
        :param bit_lsb: Least significant bit
        :return: Value of the bitfield
        """
        bitlen = bit_msb - bit_lsb + 1
        regval = self.reg_read(reg_addr)
        bitmask = ((2 ** bitlen) - 1) << bit_lsb
        return (regval & bitmask) >> bit_lsb

    @property
    def state_wr_0(self):
        """
        Get Write Group 0 LPF and HPF State
        :return: (lpf state, hpf state)
        :rtype: int tuple size 2
        """
        regval = self.reg_read(self.WR0_FILTER_REG)
        lpf = regval & self.WR0_FILTER_LPF_MASK
        hpf = (regval >> self.WR0_FILTER_HPF_SHIFT) & self.WR0_FILTER_HPF_MASK
        return (lpf, hpf)

    @state_wr_0.setter
    def state_wr_0(self, coefs):
        """
        Set Write Group 0 LPF and HPF State
        :param coefs: (lpf state, hpf state)
        :type coefs: int array size 2
        """
        lpf = coefs[0]
        hpf = coefs[1]
        self.reg_write(self.WR0_FILTER_REG, (hpf << self.WR0_FILTER_HPF_SHIFT) + lpf)

    @property
    def band_wr_0(self):
        """
        Get the Write Group 0 LPF and HPF switch positions and filter bands
        :return: (lpf, hpf)
        """
        regval = self.reg_read(self.WR0_SW_REG)
        lpf = regval & self.WR0_SW_OUT_MASK
        hpf = (regval >> self.WR0_SW_IN_SHIFT) & self.WR0_SW_IN_MASK
        return (lpf, hpf)

    @band_wr_0.setter
    def band_wr_0(self, coefs):
        """
        Set the Write Group 0 LPF and HPF switch positions and filter bands
        :param coefs: (lpf band, hpf band)
        :type coefs: int array size 2
        """
        lpf = coefs[0]
        hpf = coefs[1]
        self.reg_write(self.WR0_SW_REG, (self.WR0_SW_SET_VAL << self.WR0_SW_SET_SHIFT) + (hpf << self.WR0_SW_IN_SHIFT) + lpf)
        self.state_wr_0 = (0, 0)

    def create_arb_filt(self, coefs):
        """
        Set write group 0 filter parameters

        :param coefs: lpf state, hpf state, lpf band, hpf band
        :type coefs: int array size 4
        """
        self.band_wr_0 = (coefs[-2], coefs[-1])
        self.state_wr_0 = (coefs[0], coefs[1])

    def readback_all(self):
        for r in range(self.MAX_REG_ADDR):
            print(f'Reading {hex(r)} = {self.reg_read(r)}')

    def program_init_file(self, initFile):
        """
        Initialize ADMV8818 with a series of register writes from given file
        :param initFile: Filepath to text file of register writes
        """
        lineCount = 0
        with open(initFile, "r") as fptr:
            for line in fptr:
                instr = line.split()
                self.reg_write(int(instr[0], 16), int(instr[1], 16))
                time.sleep(0.1)
                print('ADMV8818 Loading Line Count ' + str(lineCount) + '                       \r', end='', flush=True)
                lineCount = lineCount + 1

        print('\n\t ADMV8818 Spi Test Status:' + str(self.spi_test()))

    def spi_test(self):
        """
        SPI test function that attempts to read register 0x5, and returns True or False
        """
        val = self.reg_read(self.PRODUCT_ID_H_REG)
        return val == self.PRODUCT_ID_H_VALUE