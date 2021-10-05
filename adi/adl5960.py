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

from adi.attribute import attribute
from adi.context_manager import context_manager


class adl5960(attribute, context_manager):
    """ADL5960 10 MHz to 20 GHz, Integrated Vector Network Analyzer Front-End

    parameters:
        uri: type=string
            URI of IIO context with ADL5960
    """

    _device_name = "adl5960"

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._device_name = device_name
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADL5960 device not found")

    # Temp Sensor

    @property
    def temperature(self):
        """Get the temperature reading in °C"""
        return self._get_iio_attr("temp0", "input", False, self._ctrl) / 1000

    # LO input

    @property
    def lo_frequency(self):
        """Get/Set the frequency in Hz"""
        return self._get_iio_attr("altvoltage0", "frequency", False, self._ctrl)

    @property
    def lo_mode_available(self):
        """Get available LO modes"""
        return self._get_iio_attr_str(
            "altvoltage0", "mode_available", False, self._ctrl
        )

    @property
    def lo_mode(self):
        """Get/Set LO mode"""
        return self._get_iio_attr_str("altvoltage0", "mode", False, self._ctrl)

    @lo_mode.setter
    def lo_mode(self, value):
        """Get/Set LO mode"""
        self._set_iio_attr("altvoltage0", "mode", False, value, self._ctrl)

    # Offset input

    @property
    def offset_frequency(self):
        """Get/Set the offset frequency in Hz"""
        return self._get_iio_attr("altvoltage1", "offset_frequency", False, self._ctrl)

    @offset_frequency.setter
    def offset_frequency(self, value):
        """Get/Set the offset frequency in Hz"""
        self._set_iio_attr_int(
            "altvoltage1", "offset_frequency", False, int(value), self._ctrl
        )

    @property
    def if_frequency(self):
        """Get/Set the IF frequency in Hz"""
        return self._get_iio_attr("altvoltage1", "if_frequency", False, self._ctrl)

    @if_frequency.setter
    def if_frequency(self, value):
        """Get/Set the IF frequency in Hz"""
        self._set_iio_attr_int(
            "altvoltage1", "if_frequency", False, int(value), self._ctrl
        )

    @property
    def offset_mode_available(self):
        """Get available offset modes"""
        return self._get_iio_attr_str(
            "altvoltage1", "offset_mode_available", False, self._ctrl
        )

    @property
    def offset_mode(self):
        """Get/Set offset mode"""
        return self._get_iio_attr_str("altvoltage1", "offset_mode", False, self._ctrl)

    @offset_mode.setter
    def offset_mode(self, value):
        """Get/Set offset mode"""
        self._set_iio_attr("altvoltage1", "offset_mode", False, value, self._ctrl)

    # Forward

    @property
    def forward_gain(self):
        """Get/Set Forward Gain"""
        return self._get_iio_attr("voltage0", "forward_hardwaregain", True, self._ctrl)

    @forward_gain.setter
    def forward_gain(self, value):
        """Get/Set Forward Gain"""
        self._set_iio_attr_int(
            "voltage0", "forward_hardwaregain", True, int(value), self._ctrl
        )

    # Reflected

    @property
    def reflected_gain(self):
        """Get/Set Reflected Gain"""
        return self._get_iio_attr("voltage1", "reverse_hardwaregain", True, self._ctrl)

    @reflected_gain.setter
    def reflected_gain(self, value):
        """Get/Set Reflected Gain"""
        self._set_iio_attr_int(
            "voltage1", "reverse_hardwaregain", True, int(value), self._ctrl
        )

    # IF Filter cutoff

    @property
    def if_filter_cutoff(self):
        """Get/Set LPF 3db cutoff frequency (controls CIF1, CIF2)"""
        return self._get_iio_attr(
            "voltage0", "filter_low_pass_3db_frequency", True, self._ctrl
        )

    @if_filter_cutoff.setter
    def if_filter_cutoff(self, value):
        """Get/Set LPF 3db cutoff frequency (controls CIF1, CIF2)"""
        self._set_iio_attr_int(
            "voltage0", "filter_low_pass_3db_frequency", True, int(value), self._ctrl
        )

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
