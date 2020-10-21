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

from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7124(rx, context_manager):
    """ AD7124 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""
    _rx_data_type = ">u4"
    _rx_mask = 0xFFFFFF
    _rx_shift = 0

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7124-8", "ad7124-4"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the 7124 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    break
                else:
                    index += 1

        # dynamically get channels and sorting them after the index of the first voltage channel
        self._ctrl.channels.sort(key=lambda x: int(x.id[7 : x.id.find("-")]))

        for ch in self._ctrl._channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
        rx.__init__(self)

    def rx(self):
        sig = super().rx()

        if (
            self._rx_unbuffered_data
            or self._complex_data
            or self.rx_output_type == "raw"
        ):
            return sig
        else:
            mv_sig = []

            for signal in sig:
                mv_sig.append(signal / 1000)

            return mv_sig

    @property
    def sample_rate(self):
        """Sets sampling frequency of the AD7124"""
        return self._get_iio_attr(self.channel[0].name, "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        for ch in self.channel:
            self._set_iio_attr(ch.name, "sampling_frequency", False, value)

    @property
    def scale_available(self):
        """Provides all available scale(gain) settings for the AD7124 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    class _channel(attribute):
        """AD7124 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7124 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7124 channel scale(gain)"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def offset(self):
            """AD7124 channel offset"""
            return self._get_iio_attr(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._get_iio_attr(self.name, "offset", False, value)

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale
        _offset = self.channel[index].offset

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale + _offset

        if isinstance(val, np.ndarray):
            ret = [x * _scale + _offset for x in val]

        return ret
