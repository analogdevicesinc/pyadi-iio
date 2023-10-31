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


class adrf5740(attribute, context_manager):
    """ADRF5740, Digital Signal Attenuator with parallel GPIO control
    parameters:
    uri: type=string
        URI of IIO context with ADRF5740
    dev_name: type=string
        label of ADRF5740 as defined in device tree
    """

    def __init__(self, uri="", dev_name="adrf5740_control"):
        context_manager.__init__(self, uri, dev_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("adrf5740_control")
        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADRF5740 device not found")

        self._atten = 0
        self._D5 = 0
        self._D4 = 0
        self._D3 = 0
        self._D2 = 0
        self._dig_ctrl_input = 0

    @property
    def GPIO_attenuation(self):
        """GPIO_attenuation: Get/Set the dB Attenuation value when
        ADRF5740 is controlled by 4 GPIO channels D5-D2.
        Valid options are 0-22 with a step size of 2.
        """
        self._D5 = self._get_iio_attr("voltage3", "raw", True, self._ctrl)
        self._D4 = self._get_iio_attr("voltage2", "raw", True, self._ctrl)
        self._D3 = self._get_iio_attr("voltage1", "raw", True, self._ctrl)
        self._D2 = self._get_iio_attr("voltage0", "raw", True, self._ctrl)
        self._dig_ctrl_input = (
            (self._D5 << 3) | (self._D4 << 2) | (self._D3 << 1) | (self._D2 << 0)
        )
        if self._dig_ctrl_input == 0b0000:
            self._atten = 0.0
        elif self._dig_ctrl_input == 0b0001:
            self._atten = 2.0
        elif self._dig_ctrl_input == 0b0010:
            self._atten = 4.0
        elif self._dig_ctrl_input == 0b0011:
            self._atten = 6.0
        elif self._dig_ctrl_input == 0b0100:
            self._atten = 8.0
        elif self._dig_ctrl_input == 0b0101:
            self._atten = 10.0
        elif self._dig_ctrl_input == 0b0110:
            self._atten = 12.0
        elif self._dig_ctrl_input == 0b0111:
            self._atten = 14.0
        elif self._dig_ctrl_input == 0b1100:
            self._atten = 16.0
        elif self._dig_ctrl_input == 0b1101:
            self._atten = 18.0
        elif self._dig_ctrl_input == 0b1110:
            self._atten = 20.0
        elif self._dig_ctrl_input == 0b1111:
            self._atten = 22.0
        else:
            self._atten = 0.0
            print("Invalid bit settings for DSA attenuation!")
            return -1
        print(f"Attenuation for GPIO controlled DSA is {self._atten} dB.")
        return self._atten

    @GPIO_attenuation.setter
    def GPIO_attenuation(self, value):
        self._atten = value
        if value == 0:
            self._D5 = 0
            self._D4 = 0
            self._D3 = 0
            self._D2 = 0
        elif value == 2:
            self._D5 = 0
            self._D4 = 0
            self._D3 = 0
            self._D2 = 1
        elif value == 4:
            self._D5 = 0
            self._D4 = 0
            self._D3 = 1
            self._D2 = 0
        elif value == 6:
            self._D5 = 0
            self._D4 = 0
            self._D3 = 1
            self._D2 = 1
        elif value == 8:
            self._D5 = 0
            self._D4 = 1
            self._D3 = 0
            self._D2 = 0
        elif value == 10:
            self._D5 = 0
            self._D4 = 1
            self._D3 = 0
            self._D2 = 1
        elif value == 12:
            self._D5 = 0
            self._D4 = 1
            self._D3 = 1
            self._D2 = 0
        elif value == 14:
            self._D5 = 0
            self._D4 = 1
            self._D3 = 1
            self._D2 = 1
        elif value == 16:
            self._D5 = 1
            self._D4 = 1
            self._D3 = 0
            self._D2 = 0
        elif value == 18:
            self._D5 = 1
            self._D4 = 1
            self._D3 = 0
            self._D2 = 1
        elif value == 20:
            self._D5 = 1
            self._D4 = 1
            self._D3 = 1
            self._D2 = 0
        elif value == 22:
            self._D5 = 1
            self._D4 = 1
            self._D3 = 1
            self._D2 = 1
        else:
            print(
                "Please choose a valid value for attenuation (0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0 or 22.0)."
            )
            return
        print(f"Setting attenuation for GPIO controlled DSA to {value} dB.")
        self._set_iio_attr("voltage3", "raw", True, self._D5, self._ctrl)
        self._set_iio_attr("voltage2", "raw", True, self._D4, self._ctrl)
        self._set_iio_attr("voltage1", "raw", True, self._D3, self._ctrl)
        self._set_iio_attr("voltage0", "raw", True, self._D2, self._ctrl)
