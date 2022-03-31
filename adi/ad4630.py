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


import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


def _sign_extend(value, nbits):
    sign_bit = 1 << (nbits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def _bitmask(nbits):
    mask = 0
    for i in range(0, nbits):
        mask = (mask << 1) | 1
    return mask


class ad4630(rx, context_manager, attribute):
    """ AD4630 is low power 24-bit precision SAR ADC """

    _complex_data = False
    _data_type = "voltage"
    _device_name = ""
    _rx_channel_names = []
    _rx_data_type = np.uint32

    """ Default part to initialize is ad4630-24. If you don't hardware test fails"""

    def __init__(self, uri="", device_name="ad4630-24"):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4630-16", "ad4630-24", "ad4030-24"]

        if device_name not in compatible_parts:
            raise Exception(
                "Not a compatible device: "
                + device_name
                + ". Please select from "
                + str(compatible_parts)
            )
        else:
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)

        _channels = []
        self.output_bits = [ch.data_format.bits for ch in self._ctrl.channels]
        self._has_common = False
        self._is_dual = None
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            if "common" in ch.name:
                self._has_common = True
            if "differential" in ch.name:
                _channels.append((ch.id, self._diff_channel(self._ctrl, ch.id)))
                if "0" in ch.name:
                    self.chan0 = self._diff_channel(self._ctrl, ch.name)
                if "1" in ch.name:
                    self.chan1 = self._diff_channel(self._ctrl, ch.name)

        self._is_dual = (len(self._ctrl.channels) == 4) or (len(self._ctrl.channels) == 2 and not self._has_common)

        rx.__init__(self)

    def rx(self):

        if not self._rx__rxbuf:
            self._rx_init_channels()
        self._rx__rxbuf.refill()
        buff = np.frombuffer(self._rx__rxbuf.read(), dtype=np.uint32)
        data = [buff[0::2], buff[1::2]]
        temp = []

        if self._has_common:
            for ch in range(0, self._num_rx_channels):
                nbits = self._ctrl.channels[ch].data_format.bits
                shift = self._ctrl.channels[ch].data_format.shift
                ch_data = np.zeros(data[int(ch / 2)].shape, dtype=np.uint32)
                for index in range(0, len(data[int(ch / 2)])):
                    ch_data[index] = (data[int(ch / 2)][index] >> shift) & _bitmask(
                        nbits
                    )
                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
            data = temp
        else:
            if not self._is_dual:
                data = [data[0]]
            for idx, ch_data in enumerate(data):
                nbits = self._ctrl.channels[idx].data_format.bits
                shift = self._ctrl.channels[idx].data_format.shift
                if nbits == 32:
                    nbits += 1
                data[idx] = [((x >> shift) & _bitmask(nbits)) for x in data[idx]]
                temp.append(np.vectorize(_sign_extend)(data[idx], nbits))
            data = temp

        return data

    @property
    def output_data_mode(self):
        """Determine the output data mode in which device is configured."""
        if self.output_bits[0] == 30:
            return "30bit_avg"
        if self.output_bits[0] == 32:
            return "32bit_test_pattern"

        if self._has_common:
            if self.output_bits[0] == 16:
                return "16bit_diff_8bit_cm"
            if self.output_bits[0] == 24:
                return "24bit_diff_8bit_cm"

        if not self._has_common:
            if self.output_bits[0] == 16:
                return "16bit_dif"
            if self.output_bits[0] == 24:
                return "24bit_diff"

    @property
    def sample_rate(self):
        """Get/Set the sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, rate):
        """Get/Set the sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", str(rate))

    @property
    def operating_mode_avail(self):
        """Get list of all the operating mode available."""
        return self._get_iio_dev_attr_str("operating_mode_available")

    @property
    def operating_mode(self):
        """Get/Set the operating mode."""
        return self._get_iio_dev_attr_str("operating_mode")

    @operating_mode.setter
    def operating_mode(self, mode):
        """Get/Set the operating mode."""
        if mode in self.operating_mode_avail:
            self._set_iio_dev_attr_str("operating_mode", mode)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.operating_mode_avail)
            )

    @property
    def sample_averaging_avail(self):
        """Get list of all the sample averaging values available. Only available in 30bit averaged mode."""
        return self._get_iio_dev_attr("sample_averaging_available")

    @property
    def sample_averaging(self):
        """Get/Set the sample averaging. Only available in 30bit averaged mode."""
        return self._get_iio_dev_attr_str("sample_averaging")

    @sample_averaging.setter
    def sample_averaging(self, n_sample):
        """Get/Set the sample averaging. Only available in 30bit averaged mode."""
        if str(self.sample_averaging) != "OFF":
            if str(n_sample) in str(self.sample_averaging_avail):
                self._set_iio_dev_attr("sample_averaging", str(n_sample))
            else:
                raise ValueError(
                    "Error: Number of avg samples not supported \nUse one of: "
                    + str(self.sample_averaging_avail)
                )
        else:
            raise Exception("Sample Averaging only available in 30bit averaged mode.")

    class _diff_channel(attribute):
        """AD463x differential channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def hw_gain(self):
            """Get/Set the hardwaregain of differential channel."""
            return self._get_iio_attr(self.name, "hardwaregain", False)

        @hw_gain.setter
        def hw_gain(self, gain):
            """Get/Set the hardwaregain of differential channel."""
            self._set_iio_attr(self.name, "hardwaregain", False, int(gain))

        @property
        def offset(self):
            """Get/Set the offset of differential channel."""
            return self._get_iio_attr(self.name, "offset", False, self._ctrl)

        @offset.setter
        def offset(self, offset):
            """Get/Set the offset of differential channel."""
            self._set_iio_attr(self.name, "offset", False, int(offset), self._ctrl)
