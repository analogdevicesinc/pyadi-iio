# Copyright (C) 2020 Analog Devices, Inc.
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


class mwpicore(attribute, context_manager):
    """MathWorks IP HDL DUT"

    parameters:
        uri: type=string
            URI of IIO context with GPIO pins
        name: type=string
            String identifying the device by name from the device tree.
            Dynamic class properties will be created for each channel.
    """

    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)
        compatible_parts = ["mwipcore0:mmwr-channel0", "mwipcore0:mmrd-channel1"]

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        self._ctrl = None
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                break

    def axi4_lite_register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_dev_attr_str("reg_access", "enabled", self._ctrl)
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        ret = self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)
        self._set_iio_dev_attr_str("reg_access", "disabled", self._ctrl)
        return ret

    def axi4_lite_register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_dev_attr_str("reg_access", "enabled", self._ctrl)
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
        self._set_iio_dev_attr_str("reg_access", "disabled", self._ctrl)

    def check_matlab_ip(self): 
        """Check if the design has the Simulink HDL DUT IP"""
        sysid_string = str(self._ctx.attrs)

        return ("matlab") in sysid_string
