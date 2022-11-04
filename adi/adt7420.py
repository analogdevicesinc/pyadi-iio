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


class adt7420(attribute, context_manager):

    _device_name = "adt7420"

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception("ADT7420 device not found")

        self.temp = self._channel(self._ctrl, "temp")

    class _channel(attribute):
        """ADT7420 Channel"""

        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def temp_val(self):
            """ ADT7420 Channel Temperature Value """
            return self._get_iio_attr(self.name, "temp", False)

        @property
        def temp_max(self):
            """ ADT7420 Channel Max Temperature """
            return self._get_iio_attr(self.name, "temp_max", False)

        @temp_max.setter
        def temp_max(self, value):
            """ ADT7420 Channel Max Temperature """
            return self._set_iio_attr(self.name, "temp_max", False, value)

        @property
        def temp_min(self):
            """ ADT7420 Channel Min Temperature """
            return self._get_iio_attr(self.name, "temp_min", False)

        @temp_min.setter
        def temp_min(self, value):
            """ ADT7420 Channel Min Temperature """
            return self._set_iio_attr(self.name, "temp_min", False, value)

        @property
        def temp_crit(self):
            """ ADT7420 Channel Critical Temperature """
            return self._get_iio_attr(self.name, "temp_crit", False)

        @temp_crit.setter
        def temp_crit(self, value):
            """ ADT7420 Channel Critical Temperature """
            return self._set_iio_attr(self.name, "temp_crit", False, value)

        @property
        def temp_hyst(self):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._get_iio_attr(self.name, "temp_hyst", False)

        @temp_hyst.setter
        def temp_hyst(self, value):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._set_iio_attr(self.name, "temp_hyst", False, value)
