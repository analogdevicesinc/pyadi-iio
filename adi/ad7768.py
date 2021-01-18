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

from adi.context_manager import context_manager
from adi.rx_tx import rx
import numpy as np

def _cast32(sample):
            sample = sample & 0xFFFFFF
            return (sample if not (sample & 0x800000) else sample - 0x1000000)

class ad7768(rx, context_manager):
    """ AD7768 Simultaneous Sampling ADC """

    _rx_data_type = np.int32
    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3",
                         "voltage4", "voltage5", "voltage6", "voltage7"]
    _data_type = "voltage"
    _device_name = " "

    def __init__(self, uri="ip:analog.local", ):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ad7768")
        self._rxadc = self._ctx.find_device("ad7768")
        self._device_name = "ad7768"
        if not self._rxadc:
            self._ctrl = self._ctx.find_device("cf_axi_adc")
            self._rxadc = self._ctx.find_device("cf_axi_adc")
            self._device_name = "cf_axi_adc"

        rx.__init__(self)
        self.rx_buffer_size = 400

    def rx(self):
        data = np.array(rx.rx(self))
        n_sample = data.shape[1]
        if (self._device_name == "cf_axi_adc"):
            data = [_cast32(sample) for channel in data for sample in channel]
        data = np.reshape(data, (-1, n_sample))
        if (self._data_type == "voltage"):
            data = data * float(self._get_iio_attr("voltage0", "scale", False)) / 1000

        return data

    @property
    def sample_rate(self):
        return self._get_iio_dev_attr("sampling_frequency")

    @property
    def sample_rate_avail(self):
        return self._get_iio_dev_attr("sampling_frequency_available")

    @sample_rate.setter
    def sample_rate(self, rate):
        if (rate in self.sample_rate_avail):
            self._set_iio_dev_attr("sampling_frequency", rate)
        else:
            raise ValueError(
            "Error: Sample rate not supported \nUse one of: " +
            str(self.sample_rate_avail)
        )

    @property
    def power_mode(self):
        return self._get_iio_dev_attr_str("power_mode")

    @property
    def power_mode_avail(self):
        return self._get_iio_dev_attr_str("power_mode_available")

    @power_mode.setter
    def power_mode(self, mode):
        if mode in self.power_mode_avail:
            self._set_iio_dev_attr_str("power_mode", mode)
        else:
            raise ValueError(
            "Error: Power mode not supported \nUse one of: " +
            str(self.power_mode_avail)
        )

    @property
    def filter(self):
        return self._get_iio_dev_attr_str("filter_type")

    @property
    def filter_type_avail(self):
        return self._get_iio_dev_attr_str("filter_type_available")

    @filter.setter
    def filter(self, ftype):
        if ftype in self.filter_type_avail:
            self._set_iio_dev_attr_str("filter_type", ftype)
        else:
            raise ValueError(
            "Error: Filter type not supported \nUse one of: " +
            str(self.filter_type_avail)
        )

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type
