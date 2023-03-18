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

from decimal import Decimal

import numpy as np
from adi.ad7689 import ad7689
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7690(ad7689):

    _is_single_channel = True

    def __init__(self, uri="", device_name=""):

        compatible_parts = ["ad7690", "ad7980"]

        if not device_name:
            device_name = compatible_parts[0]

        if device_name in compatible_parts:

            context_manager.__init__(self, uri, device_name)

            for device in self._ctx.devices:
                if device.name == device_name:
                    self._ctrl = device
                    self._rxadc = device
                    break

            rx.__init__(self)

            self._is_single_channel = True

        else:
            try:
                super().__init__(uri=uri, device_name=device_name)
                self._is_single_channel = False
                self.rx_enabled_channels = [0]
            except Exception as exc:
                raise exc

        self.unbuffered = True

    @property
    def raw(self):
        """AD7690 channel raw value"""
        if self._is_single_channel:
            return self._get_iio_dev_attr("raw")
        else:
            return getattr(super().channel[0], "raw")

    @property
    def scale(self):
        """AD7690 channel scale getter"""
        if self._is_single_channel:
            return float(self._get_iio_dev_attr_str("scale"))
        else:
            return getattr(super().channel[0], "scale")

    @scale.setter
    def scale(self, value):
        """AD7690 channel scale setter"""
        if self._is_single_channel:
            self._set_iio_dev_attr("scale", str(Decimal(value).real))
        else:
            setattr(super().channel[0], "scale", value)

    @property
    def unbuffered(self):
        """ Get rx unbuffered flag value """
        return self._rx_unbuffered_data

    @unbuffered.setter
    def unbuffered(self, value):
        """ Set rx unbuffered flag value """
        self._rx_unbuffered_data = value

    def to_volts(self, val):
        """Converts raw value to SI"""

        ret = None

        if self._is_single_channel:

            _scale = self.scale

            if isinstance(val, np.int16):
                ret = val * _scale

            if isinstance(val, np.ndarray):
                ret = [x * _scale for x in val]

        else:
            ret = super().to_volts(0, val)

        return ret
