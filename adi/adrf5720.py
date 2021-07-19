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

from adi.attribute import attribute
from adi.context_manager import context_manager

class adrf5720(context_manager, attribute):
    """ ADRF5720 Digital Attenuator """

    _complex_data = False
    channel = "voltage0"
    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        # Dictionary with all compatible parts. The key of each entry is the device's id and it's value
        # is the number of bits the device supports.
        compatible_parts = ["adrf5720", "adrf5730", "adrf5731",]

        self._ctrl = None

        for device in self._ctx.devices:
            if device.name in compatible_parts:
                self._ctrl = device
                break

    @property
    def attenuation(self):
        """Sets attenuation of the ADRF5720"""
        return self._get_iio_attr(self.channel, "hardwaregain", True, self._ctrl)

    @attenuation.setter
    def attenuation(self, value):
        for ch in self.channel:
            # Using set_iio_attr to set attenuation writes value=-31.5-input. 
            # Adding this to reflect desired property value to device attribute.
            write_value=-31.5-value 
            self._set_iio_attr(self.channel, "hardwaregain", True, write_value, self._ctrl)
            