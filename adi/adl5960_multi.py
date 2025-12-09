# Copyright (C) 2025 Analog Devices, Inc.
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
from adi.adl5960 import adl5960

class adl5960_multi(attribute, context_manager, adl5960):
    """Multi ADL5960 control for configuring many VNA Front-Ends at the same time
    
    parameters:
        uri: type=string
            URI of IIO context with ADL5960s
        device_names: type=array
            Array of strings defining all VNA Front-End endpoints
    """

    def __init__(self, uri="", device_names=[]):
        
        self.frontends = []

        if len(device_names) == 0:
            raise Exception("adl5960_multi: No valid device names given")

        for i, device_name in enumerate(device_names):
            try:
                fe = adl5960(uri=uri, device_name=device_name)
                self.frontends.append(fe)

            except Exception:
                raise Exception(f"adl5960_multi: Failed to instantiate `{device_name}`")

        _soft_reset = False

    @property
    def frontends(self) -> list:
        """ Get the list of ADL5960 devices """
        return self.frontends

    @property
    def ifmode(self) -> str:
        """ Get the IF mode of the frontend(s) """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        return self.frontends[0].offset_mode

    @ifmode.setter
    def ifmode(self, mode):
        """ Set the IF mode for all frontend(s) """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        _valid_modes = self.frontends[0].offset_mode_available
        if mode not in _valid_modes:
            raise Exception(f"adl5960_multi: `{mode}` is not a valid IF mode") 

        for frontend in self.frontends:
            frontend.offset_mode = mode

    @property
    def lomode(self) -> str:
        """ Get the LO mode of the frontend(s) """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        return self.frontends[0].lo_mode

    @lomode.setter
    def lomode(self, mode):
        """ Set the LO mode for all frontend(s) """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        _valid_modes = self.frontends[0].lo_mode_available
        if mode not in _valid_modes:
            raise Exception(f"adl5960_multi: `{mode}` is not a valid LO mode")

        for frontend in self.frontends:
            frontend.lo_mode = mode

    @property
    def corner_freq_filt_2x(self) -> int:
        """ Get corner frequency of filter in 2x freq multiplier in LO interface """
        data = self.reg_read(0x21)
        return data & 0x1F

    @corner_freq_filt_2x.setter
    def corner_freq_filt_2x(self, val):
        """ Set corner frequency of filter in 2x freq multiplier in LO interface """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        data = self.reg_read(0x21)
        data = (data & 0xE0) | val
        self.multi_reg_write(0x21, data)

    @property
    def corner_freq_filt_4x(self) -> int:
        """ Get corner frequency of filter in 4x freq multiplier in LO interface """
        data = self.reg_read(0x22)
        return data & 0x1F

    @corner_freq_filt_4x.setter
    def corner_freq_filt_4x(self, val):
        """ Set corner frequency of filter in 4x freq multiplier in LO interface """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        data = self.reg_read(0x22)
        data = (data & 0xE0) | val
        self.multi_reg_write(0x22, data)

    @property
    def forward_gain(self) -> int:
        """ Get the forward gain of IF amplifier """
        return self.frontends[0].forward_gain

    @forward_gain.setter
    def forward_gain(self, val):
        """ Set the forward gain of IF amplifier """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        for frontend in self.frontends:
            frontend.forward_gain = val

    @property
    def relected_gain(self) -> int:
        """ Get the reflected gain of IF amplifier """
        return self.frontends[0].reflected_gain

    @relected_gain.setter
    def relected_gain(self, val):
        """ Set the reflected gain of IF amplifier """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        for frontend in self.frontends:
            frontend.reflected_gain = val

    @property
    def cif1(self) -> int:
        """ Get corner frequency of narrow-band IF filter """
        data = self.spi_read(0x25)
        return data & 0xf

    @cif1.setter
    def cif1(self, val):
        """ Set corner frequency of narrow-band IF filter """
        data = self.spi_read(0x25)
        data = (data & 0xf0) | val
        self.multi_reg_write(0x25, data)

    @property
    def cif2(self) -> int:
        """ Get corner frequency of narrow-band IF filter """
        data = self.spi_read(0x25)
        return data >> 4

    @cif2.setter
    def cif2(self, val):
        """ Set corner frequency of narrow-band IF filter """
        data = self.spi_read(0x25)
        val = val << 4
        data = (data & 0xf) | val
        self.multi_reg_write(0x25, data)

    @property
    def tdeg(self) -> dict:
        """ Get the thermometer readout for all front-end devices """
        readout = {}
    
        for frontend in self.frontends:
            readout[frontend._device_name] = frontend.reg_read(0x26) & 0x1f

        return readout

    @property
    def soft_reset(self):
        """ Get the software reset state (internally cached) """
        return self._soft_reset

    @soft_reset.setter
    def soft_reset(self, val):
        """ Set the software reset state """
        val = int(val) << 7
        self.multi_reg_write(0x00, val)
        self._soft_reset = bool(val >> 7)

    def multi_reg_write(self, reg, value):
        """ Direct register write to all frontend devices """
        for frontend in self.frontends:
            frontend.reg_write(reg, value)

    def reg_read(self, reg) -> int:
        """ Read back from first frontend device (assume all frontends in sync) """
        if len(self.frontends) == 0:
            raise Exception("adl5960_multi: No valid frontend devices")

        return int(self.frontends[0].reg_read(reg), 16)

