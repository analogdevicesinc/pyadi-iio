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

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad7291(context_manager):
    """ AD7291 ADC """

    _device_name = ""

    def __repr__(self):
        retstr = f"""
ad7291(uri="{self.uri}") object "{self._device_name}"
8-channel, I2C, 12-bit SAR ADC with temperature sensor

Channel layout:

voltageX.raw:              Raw 12-bit ADC code. read only for ADC channels
voltageX.scale:            ADC scale, millivolts per lsb
voltageX():                    Returns ADC reading in millivolts (read only)

temp0.raw:                      Temperature raw value
temp0.scale:                    Temperature scale value
temp0():                        Returns temperature in degrees Celsius

"""
        return retstr

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7291_1"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the 7291 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

        for ch in self._ctrl.channels:
            name = ch._id
            if "temp" in name:

                setattr(self, name, self._temp_channel(self._ctrl, name))

            else:
                name = ch._id
                setattr(self, name, self._channel(self._ctrl, name))

    class _channel(attribute):
        """AD7291 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD7291 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """AD7291 channel scale(gain)"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        def __call__(self):
            """Utility function, returns millivolts"""
            return self.raw * self.scale

    class _temp_channel(_channel):  # attribute):
        """AD7291 temperature channel"""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def mean_raw(self):
            """AD7291 channel mean_raw value"""
            return self._get_iio_attr(self.name, "mean_raw", False)

        def __call__(self):
            """Utility function, returns deg. C"""
            return self.mean_raw * self.scale / 1000
