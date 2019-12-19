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
from adi.rx_tx import rx_tx


class QuadMxFE(rx_tx, context_manager):
    """ Quad AD9081 Mixed-Signal Front End (MxFE) Evaluation Board """

    _complex_data = True
    _rx_channel_names = []
    _tx_channel_names = []
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("axi-ad9081-rx-3")
        # Devices with buffers
        self._rxadc = self._ctx.find_device("axi-ad9081-rx-3")
        self._txdac = self._ctx.find_device("axi-ad9081-tx-3")
        # Attribute only devices
        self._attenuator = self._ctx.find_device("hmc425a")
        self._rxadc0 = self._ctx.find_device("axi-ad9081-rx-0")
        self._rxadc1 = self._ctx.find_device("axi-ad9081-rx-1")
        self._rxadc2 = self._ctx.find_device("axi-ad9081-rx-2")
        self._rxadc3 = self._ctx.find_device("axi-ad9081-rx-3")
        self._clock_chip = self._ctx.find_device("hmc7043")
        self._pll0 = self._ctx.find_device("adf4371-0")
        self._pll1 = self._ctx.find_device("adf4371-1")
        self._pll2 = self._ctx.find_device("adf4371-2")
        self._pll3 = self._ctx.find_device("adf4371-3")

        # dynamically get channels
        for ch in self._rxadc.channels:
            if ch.scan_element:
                self._rx_channel_names.append(ch._id)
        for ch in self._txdac.channels:
            if ch.scan_element:
                self._tx_channel_names.append(ch._id)

        rx_tx.__init__(self)

    def _get_set(self, chan, attr, value):
        if value:
            self._set_iio_attr(self._rx_channel_names[chan], attr, False, value)
        else:
            return self._get_iio_attr(self._rx_channel_names[chan], attr, False)

    def _get_set_str(self, chan, attr, value):
        if value:
            self._set_iio_attr(self._rx_channel_names[chan], attr, False, value)
        else:
            return self._get_iio_attr_str(self._rx_channel_names[chan], attr, False)

    def rx_channel_nco_frequency(self, chan=0, value=None):
        """rx_channel_nco_frequency: '"""
        return self._get_set(chan, "channel_nco_frequency", value)

    def rx_channel_nco_gain_scale(self, chan=0, value=None):
        """rx_channel_nco_gain_scale: '"""
        return self._get_set(chan, "channel_nco_gain_scale", value)

    def rx_channel_nco_gain_scale(self, chan=0, value=None):
        """rx_channel_nco_phase: '"""
        return self._get_set(chan, "channel_nco_phase", value)

    def rx_main_nco_frequency(self, chan=0, value=None):
        """rx_main_nco_frequency: '"""
        return self._get_set(chan, "main_nco_frequency", value)

    def rx_main_nco_phase(self, chan=0, value=None):
        """rx_main_nco_phase: '"""
        return self._get_set(chan, "main_nco_phase", value)

    def rx_test_mode(self, chan=0, value=None):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn9 pn32 one_zero_toggle user pn7 pn15 pn31 ramp"""
        return self._get_set_str(chan, "test_mode ", value)

    @property
    def external_hardwaregain(self):
        """external_hardwaregain: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @external_hardwaregain.setter
    def external_hardwaregain(self, value):
        self._set_iio_attr(
            "voltage0", "hardwaregain", False, value, _ctrl=self._attenuator
        )
