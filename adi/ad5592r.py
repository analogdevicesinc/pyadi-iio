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


from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx, tx

from calendar import c
from decimal import Decimal

class ad5592r(context_manager, rx, tx):

    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri = "", device_index=0):
        context_manager.__init__(self,uri)
        compatible_parts = ["ad5592r", "ad5593r"]
        self.ctrl = None
        index=0

         # Selecting the device_index-th device from the 559XR family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    self._txdac = device
                    break
                else:
                    index += 1

        # Dynamically get channels after the index
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            self._rx_channel_names.append(name)
            if name == "temp":
                self.channel.append(self._channeltemp(self._ctrl, name, output))
            else:
                self.channel.append(self._channel(self._ctrl, name, output))
        rx.__init__(self)
        tx.__init__(self)

    class _channel(attribute):
        """AD5592r voltage channel"""

        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        def raw(self):
            """AD5592r channel raw value"""
            return self._get_iio_attr(self.name, "raw", self._output)

        @property
        def scale(self):
            """AD5592r channel scale(gain)"""
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @raw.setter
        def raw(self, value):
            if self._output == True:
                self._set_iio_attr(self.name, "raw", self._output, value)

        @scale.setter
        def scale(self, value):
            scale_available = self._get_iio_attr(self.name, "scale_available", self._output)
            for scale_available_0 in scale_available:
                if scale_available_0 == value:
                    self._set_iio_attr(self.name, "scale", self._output, str(Decimal(value).real))

    class _channeltemp(_channel):
        """AD5592r temp channel"""
        
        def __init__(self, ctrl, channel_name, output):
            super().__init__(ctrl,channel_name,output)

        @property
        def offset(self):
            """AD5592r channel temp offset value"""
            return self._get_iio_attr(self.name, "offset", self._output)