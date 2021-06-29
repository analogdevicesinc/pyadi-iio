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
import numpy as np

def _sign_extend(value, nbits):
    sign_bit = 1 << (nbits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

def _bitmask(nbits):
        mask = 0
        for i in range(0, nbits):
                mask = (mask  << 1) | 1
        return mask

class ad4630(rx, context_manager):
        """ AD4630 ADC """

        _complex_data = False
        _data_type = "voltage"
        _device_name = "ad4630-24"
        _rx_channel_names = []
        _rx_data_type = np.uint32

        def __init__(self, uri="ip:analog.local", device_name="ad4630-24"):
        
                context_manager.__init__(self, uri, self._device_name)

                self._ctrl = self._ctx.find_device(self._device_name)
                if not self._ctrl:
                        raise Exception("Cant find " + device_name)

                self._rxadc = self._ctx.find_device(self._device_name)
                self._device_name = self._device_name


                for ch in self._ctrl._channels:
                        name = ch._id
                        self._rx_channel_names.append(name)

                rx.__init__(self)

        def rx(self):

                if not self._rx__rxbuf:
                    self._rx_init_channels()
                self._rx__rxbuf.refill()
                buff = np.frombuffer(self._rx__rxbuf.read(), dtype=np.uint32)

                data = [buff[0::2], buff[1::2]]
                temp = []
                if self._num_rx_channels != 2:
                        for ch in range(0, self._num_rx_channels):
                                nbits = self._ctrl._channels[ch].data_format.bits
                                shift = self._ctrl._channels[ch].data_format.shift
                                ch_data = np.zeros(data[int(ch/2)].shape, dtype=np.uint32)
                                for index in range(0, len(data[int(ch/2)])):
                                        ch_data[index] = (data[int(ch/2)][index] >> shift) & _bitmask(nbits)
                                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
                        data = temp
                else:
                        for idx, ch_data in enumerate(data):
                                nbits = self._ctrl._channels[idx].data_format.bits
                                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
                        data = np.vectorize(_sign_extend)(data, nbits)

                return data

        @property
        def sample_rate(self):
                return self._get_iio_dev_attr("sampling_frequency")

        @property
        def sample_rate_avail(self):
                return self._get_iio_dev_attr("sampling_frequency_available")

        @sample_rate.setter
        def sample_rate(self, rate):
                if (str(rate) in str(self.sample_rate_avail)):
                        self._set_iio_dev_attr("sampling_frequency", str(rate))
                else:
                        raise ValueError(
                                "Error: Sample rate not supported \nUse one of: " +
                                str(self.sample_rate_avail))

        @property
        def operating_mode(self):
                return self._get_iio_dev_attr_str("operating_mode")

        @property
        def operating_mode_avail(self):
                return self._get_iio_dev_attr_str("operating_mode_available")

        @operating_mode.setter
        def operating_mode(self, mode):
                if mode in self.operating_mode_avail:
                        self._set_iio_dev_attr_str("operating_mode", mode)
                else:
                        raise ValueError(
                                "Error: Operating mode not supported \nUse one of: " +
                                str(self.operating_mode_avail))

        @property
        def sample_averaging(self):
                return self._get_iio_dev_attr_str("sample_averaging")

        @property
        def sample_averaging_avail(self):
                return self._get_iio_dev_attr_str("sample_averaging_available")

        @sample_averaging.setter
        def sample_averaging(self, n_sample):
                if str(n_sample) in str(self.sample_averaging_avail):
                        self._set_iio_dev_attr_str("sample_averaging", str(n_sample))
                else:
                        raise ValueError(
                                "Error: Number of avg samples not supported \nUse one of: " +
                                str(self.sample_averaging_avail))