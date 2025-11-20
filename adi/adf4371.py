# Copyright (C) 2020 Analog Devices, Inc.
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

from math import floor
from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4371(attribute, context_manager):
    """ADF4371 Microwave Wideband Synthesizer
    with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4371
    """

    _device_name = "adf4371"
    _muxout_options = (
        "tristate",
        "digital_lock",
        "charge_pump_up",
        "charge_pump_down",
        "RDIV2",
        "N_div_out",
        "VCO_test",
        "high",
        "VCO_calib_R_band",
        "VCO_calib_N_band",
    )

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4371 device not found")

    @property
    def muxout_mode(self):
        """Get/Set the MUX output mode"""
        return self._get_iio_dev_attr("muxout_mode", self._ctrl)

    @muxout_mode.setter
    def muxout_mode(self, value):
        """Get/Set the MUX output mode"""

        # Check that the value is valid
        if value.lower().strip() not in self._muxout_options:
            raise ValueError(
                f"muxout_mode of \"{value}\" is invalid. Valid options: {', '.join(self._muxout_options)}"
            )

        self._set_iio_dev_attr("muxout_mode", value, self._ctrl)

    @property
    def rf8_enable(self):
        """Get/Set the enable status of the 8GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl))
        )

    @rf8_enable.setter
    def rf8_enable(self, value):
        """Get/Set the enable status of the 8GHz RF output"""
        self._set_iio_attr("altvoltage0", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf8_frequency(self):
        """Get/Set the frequency of the 8GHz RF output"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @rf8_frequency.setter
    def rf8_frequency(self, value):
        """Get/Set the frequency of the 8GHz RF output"""
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def rf8_power(self):
        """Get/Set the power of the 8GHz RF output"""
        reg_val = self._ctrl.reg_read(0x25)
        return reg_val & 0b11

    @rf8_power.setter
    def rf8_power(self, value):
        """Get/Set the power of the 8GHz RF output"""
        reg_val = self._ctrl.reg_read(0x25)
        reg_val = (reg_val & ~0b11) | (value & 0b11)
        self._ctrl.reg_write(0x25, reg_val)

    @property
    def rfaux8_enable(self):
        """Get/Set the enable status of the Auxiliary 8GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage1", "powerdown", True, self._ctrl))
        )

    @rfaux8_enable.setter
    def rfaux8_enable(self, value):
        """Get/Set the enable status of the Auxiliary 8GHz RF output"""
        self._set_iio_attr("altvoltage1", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rfaux8_frequency(self):
        """Get/Set the frequency of the Auxiliary 8GHz RF output"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @rfaux8_frequency.setter
    def rfaux8_frequency(self, value):
        """Get/Set the frequency of the Auxiliary 8GHz RF output"""
        self._set_iio_attr("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def rfaux8_power(self):
        """Get/Set the power of the Auxiliary 8GHz RF output"""
        reg_val = self._ctrl.reg_read(0x72)
        return (reg_val >> 4) & 0b11

    @rfaux8_power.setter
    def rfaux8_power(self, value):
        """Get/Set the power of the Auxiliary 8GHz RF output"""
        reg_val = self._ctrl.reg_read(0x72)
        reg_val = (reg_val & ~(0b11 << 4)) | ((value & 0b11) << 4)
        self._ctrl.reg_write(0x72, reg_val)

    @property
    def rfaux8_vco_output_enable(self):
        """Get/Set the fundamental VCO output on the Auxiliary 8GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage1", "vco_output_enable", True, self._ctrl))
        )

    @rfaux8_vco_output_enable.setter
    def rfaux8_vco_output_enable(self, value):
        """Get/Set the fundamental VCO output on the Auxiliary 8GHz RF output"""
        self._set_iio_attr("altvoltage1", "vco_output_enable", True, 1 - int(value), self._ctrl)

    @property
    def rf16_enable(self):
        """Get/Set the enable status of the 16GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage2", "powerdown", True, self._ctrl))
        )

    @rf16_enable.setter
    def rf16_enable(self, value):
        """Get/Set the enable status of the 16GHz RF output"""
        self._set_iio_attr("altvoltage2", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf16_frequency(self):
        """Get/Set the frequency of the 16GHz RF output"""
        return self._get_iio_attr("altvoltage2", "frequency", True, self._ctrl)

    @rf16_frequency.setter
    def rf16_frequency(self, value):
        """Get/Set the frequency of the 16GHz RF output"""
        self._set_iio_attr("altvoltage2", "frequency", True, value, self._ctrl)

    @property
    def rf32_enable(self):
        """Get/Set the enable status of the 32GHz RF output"""
        return bool(
            1 - int(self._get_iio_attr("altvoltage3", "powerdown", True, self._ctrl))
        )

    @rf32_enable.setter
    def rf32_enable(self, value):
        """Get/Set the enable status of the 32GHz RF output"""
        self._set_iio_attr("altvoltage3", "powerdown", True, 1 - int(value), self._ctrl)

    @property
    def rf32_frequency(self):
        """Get/Set the frequency of the 32GHz RF output"""
        return self._get_iio_attr("altvoltage3", "frequency", True, self._ctrl)

    @rf32_frequency.setter
    def rf32_frequency(self, value):
        """Get/Set the frequency of the 32GHz RF output"""
        self._set_iio_attr("altvoltage3", "frequency", True, value, self._ctrl)

    @property
    def rf_div_sel(self):
        """Get/Set the RF divider select (bits 6:4 of register 0x24)"""
        reg_val = self._ctrl.reg_read(0x24)
        return (reg_val >> 4) & 0b111

    @rf_div_sel.setter
    def rf_div_sel(self, value):
        """Get/Set the RF divider select (bits 6:4 of register 0x24)"""
        reg_val = self._ctrl.reg_read(0x24)
        reg_val = (reg_val & ~(0b111 << 4)) | ((value & 0b111) << 4)
        self._ctrl.reg_write(0x24, reg_val)

    @property
    def temperature(self):
        """Get the temperature reading"""
        return self._get_iio_attr("temp0", "input", False)

    def set_freq_int_mode(self, frequency):
        """Put in INT mode. Calculate the N divider value (registers 0x10-0x11) for target frequency."""
        reference_frequency = 125e6 # TODO: extract real value, so not hardcoded

        # Put in integer mode
        reg_val = self._ctrl.reg_read(0x2B)
        reg_val = reg_val | (1 << 0)
        self._ctrl.reg_write(0x2B, reg_val)

        frac_regs = 0x1a
        while frac_regs >= 0x14:
            self._ctrl.reg_write(frac_regs, 0)
            frac_regs -= 1

        # Calculate PFD
        r_counter = self._ctrl.reg_read(0x1F)
        if r_counter == 0:
            r_counter = 32

        reg_val = self._ctrl.reg_read(0x22)
        t = (reg_val >> 4) & 0b1
        d = (reg_val >> 5) & 0b1

        pfd_frequency = reference_frequency * (1 + d) / (r_counter * (1 + t))

        # Calculate N divider from frequency: N = floor(freq / PFD)
        n_value = floor(frequency / pfd_frequency)

        if not (0 <= n_value <= 65535):
            raise ValueError(f"Calculated N={n_value} is out of range (0-65535). "
                             f"Target freq: {frequency}, PFD: {pfd_frequency}")

        # Write 16-bit N value to registers 0x10 (LSB) and 0x11 (MSB)
        self._ctrl.reg_write(0x11, (n_value >> 8) & 0xFF)
        self._ctrl.reg_write(0x10, n_value & 0xFF)