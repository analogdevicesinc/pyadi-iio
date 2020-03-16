# Copyright (C) 2019 Analog Devices, Inc.
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
import iio

from adi.ad916x import ad9166
from adi.context_manager import context_manager


class CN0511(ad9166):
    """ CN0511 Raspberry Pi Hat Signal Generator """

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        ad9166.__init__(self, uri=uri)
        self._amp = self._ctx.find_device("ad9166-amp")
        self._synth = self._ctx.find_device("adf4372")

    @property
    def amp_enable(self):
        """ amp_enable: Enable or Disable the CN0511 ad9166 amplifier """
        return True if (self._get_iio_dev_attr("en", _ctrl=self._amp) == 1) else False

    @amp_enable.setter
    def amp_enable(self, value=True):
        if value:
            val = 1
        else:
            val = 0
        self._set_iio_dev_attr_str("en", val, _ctrl=self._amp)

    @property
    def pump_current_code(self):
        """ pump_current_code: CN0511 ADF4372 pump current code. Values allowed:
        0-15. Represents the pump current."""
        return (self._synth.reg_read(0x1E) >> 4) & 0x0F

    @pump_current_code.setter
    def pump_current_code(self, value):
        if value <= 15 and value >= 0:
            # Power down first
            self._synth.reg_write(0x1E, 0x05)
            # Set new charge pump current (ICP_Iset) value
            self._synth.reg_write(0x1E, (value & 0x0F) << 4 | 0x08)
            self._synth.reg_write(0x10, 0x28)

    @property
    def pump_current_str(self):
        """ pump_current_str: CN0511 ADF4372 pump current value """
        return self.pump_current_available[self.pump_current_code]

    @pump_current_str.setter
    def pump_current_str(self, value):
        try:
            code = self.pump_current_available.index(value)
            self.pump_current_code = code
        except Exception:
            pass

    @property
    def pump_current_available(self):
        """ pump_current_available: CN0511 available pump currents. Returns the available
         current setting for the pump. """
        available = [
            "0.35 mA",  # CP_CURRENT = 0000
            "0.70 mA",  # CP_CURRENT = 0001
            "1.05 mA",  # CP_CURRENT = 0010
            "1.40 mA",  # CP_CURRENT = 0011
            "1.75 mA",  # CP_CURRENT = 0100
            "2.10 mA",  # CP_CURRENT = 0101
            "2.35 mA",  # CP_CURRENT = 0110
            "2.80 mA",  # CP_CURRENT = 0111
            "3.15 mA",  # CP_CURRENT = 1000
            "3.50 mA",  # CP_CURRENT = 1001
            "3.85 mA",  # CP_CURRENT = 1010
            "4.20 mA",  # CP_CURRENT = 1011
            "4.55 mA",  # CP_CURRENT = 1100
            "4.90 mA",  # CP_CURRENT = 1101
            "5.25 mA",  # CP_CURRENT = 1110
            "5.60 mA",  # CP_CURRENT = 1111
        ]
        return available
