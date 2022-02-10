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

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad6676(rx, context_manager):
    """ AD6676 Wideband IF Receiver Subsystem """

    _complex_data = True
    _rx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad6676-hpc")

        rx.__init__(self)

    @property
    def adc_frequency_chan0(self):
        return self._get_iio_attr_str("voltage0", "adc_frequency", False)

    @adc_frequency_chan0.setter
    def adc_frequency_chan0(self, value):
        self._set_iio_attr("voltage0", "adc_frequency", False, value)

    @property
    def bandwidth_chan0(self):
        return self._get_iio_attr_str("voltage0", "bandwidth", False)

    @bandwidth_chan0.setter
    def bandwidth_chan0(self, value):
        self._set_iio_attr("voltage0", "bandwidth", False, value)

    @property
    def bw_margin_high_chan0(self):
        return self._get_iio_attr_str("voltage0", "bw_margin_high", False)

    @bw_margin_high_chan0.setter
    def bw_margin_high_chan0(self, value):
        self._set_iio_attr("voltage0", "bw_margin_high", False, value)

    @property
    def bw_margin_if_chan0(self):
        return self._get_iio_attr_str("voltage0", "bw_margin_if", False)

    @bw_margin_if_chan0.setter
    def bw_margin_if_chan0(self, value):
        self._set_iio_attr("voltage0", "bw_margin_if", False, value)

    @property
    def bw_margin_low_chan0(self):
        return self._get_iio_attr_str("voltage0", "bw_margin_low", False)

    @bw_margin_low_chan0.setter
    def bw_margin_low_chan0(self, value):
        self._set_iio_attr("voltage0", "bw_margin_low", False, value)

    @property
    def hardwaregain_chan0(self):
        return self._get_iio_attr_str("voltage0", "hardwaregain", False)

    @hardwaregain_chan0.setter
    def hardwaregain_chan0(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def intermediate_frequency_chan0(self):
        return self._get_iio_attr_str("voltage0", "intermediate_frequency", False)

    @intermediate_frequency_chan0.setter
    def intermediate_frequency_chan0(self, value):
        self._set_iio_attr("voltage0", "intermediate_frequency", False, value)

    @property
    def sampling_frequency_chan0(self):
        return self._get_iio_attr_str("voltage0", "sampling_frequency", False)

    @sampling_frequency_chan0.setter
    def sampling_frequency_chan0(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", False, value)

    @property
    def shuffler_control_chan0(self):
        """Available values:
        disable fadc fadc/2 fadc/3 fadc/4
        """
        return self._get_iio_attr_str("voltage0", "shuffler_control", False)

    @shuffler_control_chan0.setter
    def shuffler_control_chan0(self, value):
        self._set_iio_attr("voltage0", "shuffler_control", False, value)

    @property
    def shuffler_thresh_chan0(self):
        """Available values:
        disable fadc fadc/2 fadc/3 fadc/4
        """
        return self._get_iio_attr_str("voltage0", "shuffler_thresh", False)

    @shuffler_thresh_chan0.setter
    def shuffler_thresh_chan0(self, value):
        self._set_iio_attr("voltage0", "shuffler_thresh", False, value)

    @property
    def test_mode_chan0(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode_chan0.setter
    def test_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def adc_frequency_chan1(self):
        return self._get_iio_attr_str("voltage1", "adc_frequency", False)

    @adc_frequency_chan1.setter
    def adc_frequency_chan1(self, value):
        self._set_iio_attr("voltage1", "adc_frequency", False, value)

    @property
    def bandwidth_chan1(self):
        return self._get_iio_attr_str("voltage1", "bandwidth", False)

    @bandwidth_chan1.setter
    def bandwidth_chan1(self, value):
        self._set_iio_attr("voltage1", "bandwidth", False, value)

    @property
    def bw_margin_high_chan1(self):
        return self._get_iio_attr_str("voltage1", "bw_margin_high", False)

    @bw_margin_high_chan1.setter
    def bw_margin_high_chan1(self, value):
        self._set_iio_attr("voltage1", "bw_margin_high", False, value)

    @property
    def bw_margin_if_chan1(self):
        return self._get_iio_attr_str("voltage1", "bw_margin_if", False)

    @bw_margin_if_chan1.setter
    def bw_margin_if_chan1(self, value):
        self._set_iio_attr("voltage1", "bw_margin_if", False, value)

    @property
    def bw_margin_low_chan1(self):
        return self._get_iio_attr_str("voltage1", "bw_margin_low", False)

    @bw_margin_low_chan1.setter
    def bw_margin_low_chan1(self, value):
        self._set_iio_attr("voltage1", "bw_margin_low", False, value)

    @property
    def hardwaregain_chan1(self):
        return self._get_iio_attr_str("voltage1", "hardwaregain", False)

    @hardwaregain_chan1.setter
    def hardwaregain_chan1(self, value):
        self._set_iio_attr("voltage1", "hardwaregain", False, value)

    @property
    def intermediate_frequency_chan1(self):
        return self._get_iio_attr_str("voltage1", "intermediate_frequency", False)

    @intermediate_frequency_chan1.setter
    def intermediate_frequency_chan1(self, value):
        self._set_iio_attr("voltage1", "intermediate_frequency", False, value)

    @property
    def sampling_frequency_chan1(self):
        return self._get_iio_attr_str("voltage1", "sampling_frequency", False)

    @sampling_frequency_chan1.setter
    def sampling_frequency_chan1(self, value):
        self._set_iio_attr("voltage1", "sampling_frequency", False, value)

    @property
    def shuffler_control_chan1(self):
        """Available values:
        disable fadc fadc/2 fadc/3 fadc/4
        """
        return self._get_iio_attr_str("voltage1", "shuffler_control", False)

    @shuffler_control_chan1.setter
    def shuffler_control_chan1(self, value):
        self._set_iio_attr("voltage1", "shuffler_control", False, value)

    @property
    def shuffler_thresh_chan1(self):
        """Available values:
        disable fadc fadc/2 fadc/3 fadc/4
        """
        return self._get_iio_attr_str("voltage1", "shuffler_thresh", False)

    @shuffler_thresh_chan1.setter
    def shuffler_thresh_chan1(self, value):
        self._set_iio_attr("voltage1", "shuffler_thresh", False, value)

    @property
    def test_mode_chan1(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage1", "test_mode", False)

    @test_mode_chan1.setter
    def test_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "test_mode", False, value, self._rxadc)
