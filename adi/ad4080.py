# Copyright (C) 2022 Analog Devices, Inc.
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


class ad4080(rx, context_manager):

    """ AD4080 ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = "ad4080"

    def __init__(self, uri=""):

        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("ad4080")
        self._ctrl = self._ctx.find_device("ad4080")

        rx.__init__(self)

    @property
    def scale(self):
        """scale: Scale value"""
        return self._get_iio_attr("voltage0", "scale", False)

    @property
    def scale_available(self):
        """scale_avaliable: Available scale value"""
        return self._get_iio_attr("voltage0", "scale_available", False)

    @property
    def sampling_frequency(self):
        """sampling_frequency: Sampling frequency value"""
        return self._get_iio_dev_attr("sampling_frequency")

    @property
    def sinc_dec_rate_available(self):
        """"""
        return self._get_iio_dev_attr("sinc_dec_rate_available", False)

    @property
    def sinc_dec_rate(self):
        """"""
        return self._get_iio_dev_attr("sinc_dec_rate", False)

    @sinc_dec_rate.setter
    def sinc_dec_rate(self, value):
        self._set_iio_dev_attr("sinc_dec_rate", value)

    @property
    def filter_sel_available(self):
        """"""
        return self._get_iio_dev_attr_str("filter_sel_available", False)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)