# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from enum import Enum

from adi.attribute import attribute
from adi.compatible import compatible


class adf4151x(attribute, compatible):
    """
    Driver for ADF41513 26.5 GHz Integer-N/Fractional-N PLL Frequency Synthesizer
    """

    class mode(Enum):
        """ADF41513 Mode Enumeration"""

        INTEGER_N = 0
        FIXED_MODULUS = 1
        VARIABLE_MODULUS = 2

    class reg(Enum):
        """ADF41513 Register Enumeration"""

        R0 = 0
        R1 = 1
        R2 = 2
        R3 = 3
        R4 = 4
        R5 = 5
        R6 = 6
        R7 = 7
        R8 = 8
        R9 = 9
        R10 = 10
        R11 = 11
        R12 = 12
        R13 = 13

    class muxout(Enum):
        """ADF41513 MUXOUT Pin Function Enumeration"""

        TRISTATE = 0x0
        DVDD = 0x1
        DGND = 0x2
        R_DIV = 0x3
        N_DIV = 0x4
        DIG_LD = 0x6
        SDO = 0x7
        READBACK = 0x8
        CLK1_DIV = 0xA
        R_DIV2 = 0xD
        N_DIV2 = 0xE

    def __init__(self, uri="", device_name=""):
        """
        Constructor for the ADF41513 class.

        :param str uri: URI of IIO context with ADF41513
        :param str device_name: name or label of the ADF41513 device
        """
        compatible.__init__(self, uri, device_name)

    @property
    def frequency(self):
        """Get/Set the output frequency value in Hz

        This value represents the output frequency of the external VCO with
        respect to the input frequency reference.
        """
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency.setter
    def frequency(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def frequency_resolution(self):
        """Get/Set the output frequency resolution value in Hz

        This value represents the desired frequency resolution of the output
        frequency, used to derive modulus and fraction values for fractional-N
        operation.
        """
        return self._get_iio_attr(
            "altvoltage0", "frequency_resolution", True, self._ctrl
        )

    @frequency_resolution.setter
    def frequency_resolution(self, value):
        self._set_iio_attr(
            "altvoltage0", "frequency_resolution", True, value, self._ctrl
        )

    @property
    def powerdown(self):
        """Get/Set the powerdown state"""
        return self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl)

    @powerdown.setter
    def powerdown(self, value):
        self._set_iio_attr("altvoltage0", "powerdown", True, value, self._ctrl)

    @property
    def locked(self):
        """Get the PLL lock status"""
        try:
            self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)
            return True
        except Exception:
            return False

    @property
    def muxout_select(self) -> "adf4151x.muxout":
        """Get/Set the MUXOUT pin function

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        muxout_sel = (self.reg_read(adf4151x.reg.R12) >> 28) & 0xF
        return adf4151x.muxout(muxout_sel)

    @muxout_select.setter
    def muxout_select(self, mux: "adf4151x.muxout"):
        reg12_val = self.reg_read(adf4151x.reg.R12)
        reg12_val &= ~(0xF << 28)
        reg12_val |= (mux.value & 0xF) << 28
        self.reg_write(adf4151x.reg.R12, hex(reg12_val))

    @property
    def charge_pump_index(self):
        """Get/Set the charge pump current index value

        This property uses register access, so it is mostly intended for
        debugging and testing purposes. The charge pump current value depends on
        the R_SET resistor value and the charge pump index value. The current
        charge pump current and resistor value can be set in the device-tree for
        production use-cases.
        """
        return (self.reg_read(adf4151x.reg.R5) >> 25) & 0xF

    @charge_pump_index.setter
    def charge_pump_index(self, index):
        r5_val = self.reg_read(adf4151x.reg.R5)
        r5_val &= ~(0xF << 25)
        r5_val |= (index & 0xF) << 25
        self.reg_write(adf4151x.reg.R5, r5_val)

    @property
    def operating_mode(self) -> "adf4151x.mode":
        """Get/Set the ADF41513 mode of operation

        This property uses register access, so it is mostly intended for
        debugging and testing purposes. The mode of operation is automatically
        determined based on frequency_resolution and frequency values.
        """
        int_mode = (self.reg_read(adf4151x.reg.R6) >> 20) & 0x1
        if int_mode == 1:
            return adf4151x.mode.INTEGER_N

        var_mode = (self.reg_read(adf4151x.reg.R0) >> 28) & 0x1
        if var_mode == 1:
            return adf4151x.mode.VARIABLE_MODULUS

        return adf4151x.mode.FIXED_MODULUS

    @operating_mode.setter
    def operating_mode(self, mode: "adf4151x.mode"):
        r0_val = self.reg_read(adf4151x.reg.R0)
        r6_val = self.reg_read(adf4151x.reg.R6)

        if mode == adf4151x.mode.INTEGER_N:
            r6_val |= 1 << 20
        else:
            r6_val &= ~(1 << 20)

        if mode == adf4151x.mode.VARIABLE_MODULUS:
            r0_val |= 1 << 28
        else:
            r0_val &= ~(1 << 28)

        self.reg_write(adf4151x.reg.R0, r0_val)
        self.reg_write(adf4151x.reg.R6, r6_val)

    @property
    def INT(self):
        """Get/Set the INT value in R0

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        return (self.reg_read(adf4151x.reg.R0) >> 4) & 0xFFFF

    @INT.setter
    def INT(self, value):
        r0_val = self.reg_read(adf4151x.reg.R0)
        r0_val &= ~(0xFFFF << 4)
        r0_val |= (value & 0xFFFF) << 4
        self.reg_write(adf4151x.reg.R0, r0_val)

    @property
    def FRAC1(self):
        """Get/Set the FRAC1 value in R1

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        return (self.reg_read(adf4151x.reg.R1) >> 4) & 0x1FFFFFF

    @FRAC1.setter
    def FRAC1(self, value):
        r1_val = self.reg_read(adf4151x.reg.R1)
        r1_val &= ~(0x1FFFFFF << 4)
        r1_val |= (value & 0x1FFFFFF) << 4
        self.reg_write(adf4151x.reg.R1, r1_val)

    @property
    def FRAC2(self):
        """Get/Set the FRAC2 value in R3

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        return (self.reg_read(adf4151x.reg.R3) >> 4) & 0xFFFFFF

    @FRAC2.setter
    def FRAC2(self, value):
        r3_val = self.reg_read(adf4151x.reg.R3)
        r3_val &= ~(0xFFFFFF << 4)
        r3_val |= (value & 0xFFFFFF) << 4
        self.reg_write(adf4151x.reg.R3, r3_val)

    @property
    def MOD2(self):
        """Get/Set the MOD2 value in R4

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        return (self.reg_read(adf4151x.reg.R4) >> 4) & 0xFFFFFF

    @MOD2.setter
    def MOD2(self, value):
        r4_val = self.reg_read(adf4151x.reg.R4)
        r4_val &= ~(0xFFFFFF << 4)
        r4_val |= (value & 0xFFFFFF) << 4
        self.reg_write(adf4151x.reg.R4, r4_val)

    @property
    def N(self):
        """Get the N divider value

        This property uses register access, so it is mostly intended for
        debugging and testing purposes.
        """
        mode = self.operating_mode
        if mode == adf4151x.mode.INTEGER_N:
            n_div = self.INT
        elif mode == adf4151x.mode.VARIABLE_MODULUS:
            n_div = self.INT + (self.FRAC1 + self.FRAC2 / self.MOD2) / (2 ** 25)
        else:
            n_div = self.INT + self.FRAC1 / (2 ** 25)
            if (self.reg_read(adf4151x.reg.R5) >> 24) & 0x1 == 0:  # LSB_P1
                n_div += 1 / (2 ** 26)

        return n_div

    def reg_read(self, reg: "adf4151x.reg"):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg.value, self._ctrl)
        return int(self._get_iio_debug_attr_str("direct_reg_access", self._ctrl), 0)

    def reg_write(self, reg: "adf4151x.reg", value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str(
            "direct_reg_access", f"{reg.value} {value}", self._ctrl
        )


# create compatible classes
adf41513 = compatible.with_class(adf4151x, "adf41513")
adf41510 = compatible.with_class(adf4151x, "adf41510")
