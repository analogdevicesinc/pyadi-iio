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

from adi.ad9250 import ad9250
from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import rx


class fmcjesdadc1(ad9250):

    """FMCJESDADC1 Four-Channel High Speed Data Acquisition FMC Board"""

    _split_cores = True
    _rx_channel_names = ["voltage0", "voltage1"]  # Recheck RX Channel Names
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):
        context_manager.__init__(self, uri, self._device_name)

        self._jesd = jesd(uri, username=username, password=password)
        self._rxadc = self._ctx.find_device("axi-ad9250-hpc-0")
        self._rxadc_chip_b = self._ctx.find_device("axi-ad9250-hpc-1")

        rx.__init__(self)

    @property
    def test_mode_chan0(self):
        """test_mode_chan0: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode_chan0.setter
    def test_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def test_mode_chan1(self):
        """test_mode_chan1: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage1", "test_mode", False)

    @test_mode_chan1.setter
    def test_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "test_mode", False, value, self._rxadc)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()
