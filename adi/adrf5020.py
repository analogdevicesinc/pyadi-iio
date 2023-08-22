# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
# Copyright (C) 2023 Analog Devices, Inc.
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


class adrf5020(attribute, context_manager):
    """ADRF5020, Digital Switch
    parameters:
    uri: type=string
        URI of IIO context with ADRF5020
    dev_name: type=string
        label of ADRF5020 as defined in device tree
    """

    def __init__(self, uri="", dev_name=""):
        context_manager.__init__(self, uri, dev_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device(dev_name)
        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADRF5020 device not found")

    @property
    def control_signal_value(self):
        """control_signal_value: Get/Set the Control voltage signal.
        Valid options are 1 or 0.
        """
        return self._get_iio_attr("voltage0", "raw", True, self._ctrl)

    @control_signal_value.setter
    def control_signal_value(self, value):
        print(f"Setting control signal input for RF switch to {value}.")
        self._set_iio_attr("voltage0", "raw", True, value, self._ctrl)
