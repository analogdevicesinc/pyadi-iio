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


class ad5686(context_manager, attribute):
    """ AD5686 DAC """

    _complex_data = False
    channel = []
    _device_name = ""
    _channel = "voltage0"
    _rx_data_type = np.int32

    def __init__(self, uri="", device_index=0):
        context_manager.__init__(self, uri, self._device_name)
        # Dictionary with all compatible parts. The key of each entry is the device's id and it's value
        # is the number of bits the device supports.
        compatible_parts = [
            "ad5310r",
            "ad5311r",
            "ad5671r",
            "ad5672r",
            "ad5673r",
            "ad5674r",
            "ad5675r",
            "ad5676",
            "ad5676r",
            "ad5677r",
            "ad5679r",
            "ad5681r",
            "ad5682r",
            "ad5683",
            "ad5683r",
            "ad5684",
            "ad5684r",
            "ad5685r",
            "ad5686",
            "ad5686r",
            "ad5691r",
            "ad5692r",
            "ad5693",
            "ad5693r",
            "ad5694",
            "ad5694r",
            "ad5695r",
            "ad5696",
            "ad5696r",
        ]

        self._ctrl = None
        index = 0
        # We are selecting the device_index-th device from the 5686 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

        self._scale = float(self._get_iio_attr_str(self._channel, "scale", True))

    @property
    def powerdown(self):
        """AD5683R channel powerdown value"""
        return self._get_iio_attr(self._channel, "raw", True)

    @powerdown.setter
    def powerdown(self, val):
        """AD5683R channel powerdown value"""
        self._set_iio_attr(self._channel, "powerdown", True, val)

    @property
    def powerdown_mode(self):
        """AD5683R channel powerdown mode value"""
        return self._get_iio_attr_str(self._channel, "powerdown_mode", True)

    @powerdown_mode.setter
    def powerdown_mode(self, val):
        """AD5683R channel powerdown value"""
        self._set_iio_attr_str(self._channel, "powerdown_mode", True, val)

    @property
    def powerdown_mode_available(self):
        """Provides all available powerdown mode settings for the AD5683r"""
        return self._get_iio_attr_str(self._channel, "powerdown_mode_available", True)

    @property
    def raw(self):
        """AD5683R channel raw value"""
        return self._get_iio_attr(self._channel, "raw", True)

    @raw.setter
    def raw(self, val):
        """AD5683R channel raw value"""
        self._set_iio_attr(self._channel, "raw", True, val)

    @property
    def scale(self):
        """AD5683R channel scale(gain)"""
        return self._scale

    def to_raw(self, val):
        """Converts raw value to SI"""
        return int(1000.0 * val / self._scale)

    @property
    def volts(self):
        """AD5683R channel value in volts"""
        return self.raw * self._scale

    @volts.setter
    def volts(self, val):
        """AD5683R channel value in volts"""
        self.raw = self.to_raw(val)
