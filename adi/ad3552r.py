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
from adi.rx_tx import tx


class ad3552r(tx, context_manager, attribute):
    """AD3552R DAC"""

    _device_name = ""
    channel = []  # type: ignore
    _complex_data = False

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)
        compatible_parts = ["axi-ad3552r-0","axi-ad3552r-1"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

                # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._txdac = device
                break

        for ch in self._ctrl.channels:
            name = ch.id
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        tx.__init__(self)

    @property
    def sample_rate(self):
        """Sample rate of the DAC"""
        return self._get_iio_dev_attr("sampling_frequency", self._txdac)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr("sampling_frequency", value, self._txdac)

    class _channel(attribute):
        """AD3552R channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD3552R channel raw value"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", True)

        @property
        def en(self):
            """AD3552R channel en value"""
            return self._get_iio_attr(self.name, "en", True)

        @en.setter
        def en(self, value):
            self._set_iio_attr(self.name, "en", True)

        @property
        def scale(self):
            """AD3552R channel scale value"""
            return self._get_iio_attr(self.name, "scale", True)

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", True)

        @property
        def offset(self):
            """AD3552R channel offset value"""
            return self._get_iio_attr(self.name, "offset", True)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", True)
