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

from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad5627(tx, context_manager):
    """ AD5627 Low Power Dual nanoDAC """

    _complex_data = False
    _tx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._txdac = self._ctx.find_device("ad5627")
        tx.__init__(self)

    @staticmethod
    def _adp_bias_volts_to_raw_convert(value, inverse):
        """Convert ADP bias from user values to internal values (or reverse)."""
        ret = 0.0
        if inverse:
            ret = -((value * 5 * 18.18) / 4096) + 122
        else:
            ret = ((-122 - value) * 4096) / (5 * 18.18)
        return ret

    @property
    def apdbias(self):
        """Get the APD Bias."""
        bias = self._get_iio_attr("voltage0", "raw", True, self._txdac)
        return self._adp_bias_volts_to_raw_convert(bias, True)

    @apdbias.setter
    def apdbias(self, value):
        """Set the APD Bias."""
        bias = self._adp_bias_volts_to_raw_convert(value, False)
        self._set_iio_attr_float("voltage0", "raw", True, bias, self._txdac)

    @staticmethod
    def _tilt_volts_to_raw_convert(value, inverse):
        """Convert tilt voltage from user values to internal values (or reverse)."""
        ret = 0.0
        if inverse:
            ret = (value * 5) / 4096
        else:
            ret = (value * 4096) / 5
        return ret

    @property
    def tiltvoltage(self):
        """Get the Tilt Voltage."""
        voltage = self._get_iio_attr("voltage1", "raw", True, self._txdac)
        return self._tilt_volts_to_raw_convert(voltage, True)

    @tiltvoltage.setter
    def tiltvoltage(self, voltage):
        """Set the Tilt Voltage."""
        voltage = self._tilt_volts_to_raw_convert(voltage, False)
        self._set_iio_attr_float("voltage1", "raw", True, voltage, self._txdac)
