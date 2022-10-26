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
from collections import OrderedDict

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2499(rx, context_manager):

    channel: OrderedDict = None
    _device_name = "ltc2499"
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ltc2499")

        if not self._ctrl:
            raise Exception("No device found")

        _channels = []
        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch.id)
            _channels.append((ch.id, self._channel(self._ctrl, ch.id)))
        self.channel = OrderedDict(_channels)

        rx.__init__(self)

    class _channel(attribute):
        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def raw(self):
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @property
        def value(self):
            return self.raw * self.scale
