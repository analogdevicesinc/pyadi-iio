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

from ast import Raise
from unicodedata import name
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
       
class ad463x(rx, context_manager):
        """ AD463X ADC """
        
        class _channel():
                _common_ch = None
                _ch_data = None

                class _data():
                        
                        _common_mode = None
                        def __init__(self, ctx, data):
                                self._ctx = ctx
                                if (data.size == 2):
                                        self._voltage = data[0]
                                        self._common_mode = data[1]
                                else:
                                        self._voltage = data
                        
                        @property
                        def common_mode_voltage(self):
                                if ( not self._common_mode):
                                        raise ValueError("No common mode data available")
                                return self._common_mode
                        
                        @property
                        def voltage(self):
                                return self._voltage
                
                def __init__(self, dev_ctx, ch_ctx, index):
                        self._dev_ctx = dev_ctx
                        self._ctx = ch_ctx
                        self._index = index
                
                @property
                def data(self):
                        self._ch_data = np.array(self._dev_ctx._data[self._index])
                        if (self._common_ch):
                                common_voltage = np.array(self._dev_ctx._data[self._index + 1])
                                self._ch_data = np.dstack((self._ch_data, common_voltage))[0]
                        
                        return [self._data(self, pair) for pair in self._ch_data]

                @property
                def hardwaregain(self):
                        if (len(self._ctx.attrs) == 0):
                                raise ValueError("The selected channel does not support hardwaregain")
                        return self._dev_ctx._get_iio_attr(self._ctx._name, "hardwaregain", True)
                
                @hardwaregain.setter
                def hardwaregain(self, val):
                        if (len(self._ctx.attrs) == 0):
                                raise ValueError("The selected channel does not support hardwaregain")
                        if (round(val) not in range(0, 2)):
                                print(f"{val} is an invalid gain value. Epexcted values between 0 and 2")
                        return self._dev_ctx._set_iio_attr(self._ctx._name, "hardwaregain", True, val)
                        
                @property
                def offset(self):
                        if (len(self._ctx.attrs) == 0):
                                raise ValueError("The selected channel does not support offset settings")
                        return self._dev_ctx._get_iio_attr(self._ctx._name, "offset", True)
                
                @offset.setter
                def offset(self, val):
                        if (len(self._ctx.attrs) == 0):
                                raise ValueError("The selected channel does not support offsetsettings")
                        if (val not in range(-8388607, 8388607)):
                                print(f"{val} is an invalid gain value. Epexcted values between -8388607 and 8388607")
                        return self._dev_ctx._set_iio_attr(self._ctx._name, "offset", True, val)
                        
                
        channels = [None,None]

        __supported_devices = ["ad4030-24", "ad4630-24"]
        _lane_modes = ["one lane per channel", "two lanes per channel",
                       "four lanes per channel", "interleaved"]
        _clock_modes = ["SPI clocking mode", "Echo clock mode",
                       "Master clock mode"]
        _ddr_modes = ["SDR", "DDR"]
        _out_modes = ["24-bit differential data",
                      "16-bit differential data + 8-bit common mode data",
                      "24-bit differential data + 8-bit common mode data",
                      "30-bit averaged differential data + OR-bit + SYNC-bitsssss",
                      "32-bit test data pattern"]
        _device_config = []
        _data = []
        _complex_data = False
        _data_type = "voltage"
        _device_name = ""
        _rx_channel_names = []
        _rx_data_type = np.uint32
        
        def __get_device_info(self):
                self._set_iio_debug_attr_str("direct_reg_access", 0x20)
                reg = int(self._get_iio_debug_attr_str("direct_reg_access"), base=16)
                self._device_config = [
                        self._lane_modes[int(reg >> 6) & 0x03],
                        self._clock_modes[int(reg >> 4) & 0x03],
                        self._ddr_modes[int(reg >> 3) & 0x01],
                        self._out_modes[int(reg) & 0x07]
                ]

        def __find_device(self, uri="ip:analog.local", device_name=_device_name):
                if (not device_name):
                        for device in self.__supported_devices:
                                context_manager.__init__(self, uri, device)
                                self._ctrl = self._ctx.find_device(device)
                                if self._ctrl:
                                        self._device_name = device
                                        self._rxadc = self._ctx.find_device(self._device_name)
                                        break
                        if not self._ctrl:
                                raise Exception("Coudln't find a compatible device")
                else:
                        self._device_name = device_name
                        context_manager.__init__(self, uri, self._device_name)
                        self._ctrl = self._ctx.find_device(self._device_name)
                        if not self._ctrl:
                                raise Exception("Cant find " + device_name)

                        self._rxadc = self._ctx.find_device(self._device_name)

        def __init__(self, uri="ip:analog.local", device_name=_device_name):
                self.__find_device(uri,device_name)
                self.__get_device_info()
                
                for idx, ch in enumerate(self._ctrl._channels):
                        self._rx_channel_names.append(ch._id)
                        ch_index = (int)(ch.name[-1])
                        if ch.data_format.bits != 8:
                                self.channels[ch_index] = self._channel(self, ch, idx)
                        else:
                                self.channels[ch_index]._common_ch = ch
                if not self.channels[1]:
                        self.channels = [self.channels[0]]
                rx.__init__(self)

        def rx(self):
                """
                The storage buffer is 64-bit wide and is distributed as following :
                        Buffer   = [0 ... 31  32 ... 63]
                        Channel0 = [0 ... 31]
                        Channel1 =           [32 ... 63]
                """
                if not self._rx__rxbuf:
                    self._rx_init_channels()
                self._rx__rxbuf.refill()
                buff = np.frombuffer(self._rx__rxbuf.read(), dtype=np.uint32)
                data = [buff[0::2], buff[1::2]]
                temp = []
                # if the mode has diff+common voltage
                if (self._device_config[3] == self._out_modes[1] or
                    self._device_config[3] == self._out_modes[2]):
                        for ch in range(0, self._num_rx_channels):
                                nbits = self._ctrl._channels[ch].data_format.bits
                                shift = self._ctrl._channels[ch].data_format.shift
                                ch_data = np.zeros(data[int(ch/2)].shape, dtype=np.uint32)
                                for index in range(0, len(data[int(ch/2)])):
                                        ch_data[index] = (data[int(ch/2)][index] >> shift) & _bitmask(nbits)
                                if (shift == 0):
                                        nbits += 1
                                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
                        data = temp
                else:
                        for idx, ch in enumerate(self._ctrl._channels):
                                shift = ch.data_format.shift
                                nbits = ch.data_format.bits
                                if (nbits == 32):
                                        nbits += 1
                                data[idx] = [((x >> shift) & _bitmask(nbits)) for x in data[idx]]
                                temp.append(np.vectorize(_sign_extend)(data[idx], nbits))
                        data = temp

                self._data = data
                return data

        @property
        def has_common_voltage(self):
                return (self._device_config[3] == self._out_modes[1] or
                        self._device_config[3] == self._out_modes[2])
        @property
        def name(self):
                return self._device_name

        @property
        def sample_rate(self):
                return self._get_iio_dev_attr("sampling_frequency")

        @sample_rate.setter
        def sample_rate(self, rate):
                if (rate > 0 and rate <= 2000000):
                        self._set_iio_dev_attr("sampling_frequency", str(rate))
                else:
                        raise ValueError("Error: Sample rate not supported")

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