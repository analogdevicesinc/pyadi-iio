# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from enum import Enum

from adi.attribute import attribute
from adi.device_base import device_base


class adf4151x(attribute, device_base):
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
        Constructor for the ADF4151x class.

        Args:
            uri (str): URI of IIO context with ADF4151x
            device_name (str): name, label or device ID of the ADF4151x device
        """
        device_base.__init__(self, device_name=device_name, uri=uri)

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
    def phase(self):
        """Get/Set the phase adjust value in radians

        Phase adjust increases the phase of the output relative to the current
        phase.
        """
        return self._get_iio_attr("altvoltage0", "phase", True, self._ctrl)

    @phase.setter
    def phase(self, value):
        self._set_iio_attr("altvoltage0", "phase", True, value, self._ctrl)

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
adf41510 = device_base.variant(adf4151x, "adf41510")
adf41513 = device_base.variant(adf4151x, "adf41513")
