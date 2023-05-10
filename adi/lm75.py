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


class lm75(context_manager, attribute):

    """ LM75 Temperature Sensor

    Parameters
    ----------
    uri: type=string
        Context URI. Default: Empty (auto-scan)
    device_index: type=integer
        Device index in contexts with multiple LM75 compatible devices. Default: 0
    returns:
        LM75 compatible device
    """

    _device_name = ""

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["lm75", "adt75"]

        self._ctrl = None
        index = 0
        # Select the device_index-th device from the lm75 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

    @property
    def update_interval(self):
        """Update Interval"""
        return self._get_iio_dev_attr("update_interval")

    def to_degrees(self, value):
        """Convert raw to degrees Celsius"""
        return value / 1000.0

    def to_millidegrees(self, value):
        """Convert degrees Celsius to millidegrees"""
        return int(value * 1000.0)

    @property
    def input(self):
        """LM75 temperature input value"""
        return self._get_iio_attr("temp1", "input", False)

    @property
    def max(self):
        """LM75 temperature max value"""
        return self._get_iio_attr("temp1", "max", False)

    @max.setter
    def max(self, value):
        """LM75 temperature max value"""
        return self._set_iio_attr("temp1", "max", False, value)

    @property
    def max_hyst(self):
        """LM75 max_hyst value"""
        return self._get_iio_attr("temp1", "max_hyst", False)

    @max_hyst.setter
    def max_hyst(self, value):
        """LM75 max_hyst value"""
        return self._set_iio_attr("temp1", "max_hyst", False, value)

    def __call__(self):
        """Utility function, returns deg. C"""
        return self.input / 1000
