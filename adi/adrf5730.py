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


class adrf5730(attribute, context_manager):
    """ADRF5730, Digital Signal Attenuator with parallel GPIO control
    parameters:
    uri: type=string
        URI of IIO context with ADRF5730
    dev_name: type=string
        label of ADRF5730 as defined in device tree
    """

    def __init__(self, uri="", dev_name="adrf5730_control"):
        context_manager.__init__(self, uri, dev_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("adrf5730_control")
        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADRF5730 device not found")

        self._atten_decimal = 0
        self._atten_dB = 0
        self._D5 = 0
        self._D4 = 0
        self._D3 = 0
        self._D2 = 0
        self._D1 = 0
        self._D0 = 0

    @property
    def GPIO_attenuation(self):
        """GPIO_attenuation: Get/Set the Attenuation Decimal value when
        ADRF5730 is controlled by 6 GPIO channels D5-D0.
        Valid options are 0-63 with a step size of 1.
        """
        atten_D5_dB = 0
        atten_D4_dB = 0
        atten_D3_dB = 0
        atten_D2_dB = 0
        atten_D1_dB = 0
        atten_D0_dB = 0
        self._D5 = self._get_iio_attr("voltage5", "raw", True, self._ctrl)
        self._D4 = self._get_iio_attr("voltage4", "raw", True, self._ctrl)
        self._D3 = self._get_iio_attr("voltage3", "raw", True, self._ctrl)
        self._D2 = self._get_iio_attr("voltage2", "raw", True, self._ctrl)
        self._D1 = self._get_iio_attr("voltage1", "raw", True, self._ctrl)
        self._D0 = self._get_iio_attr("voltage0", "raw", True, self._ctrl)
        if self._D5 == 1:
            atten_D5_dB = 16
        if self._D4 == 1:
            atten_D4_dB = 8
        if self._D3 == 1:
            atten_D3_dB = 4
        if self._D2 == 1:
            atten_D2_dB = 2
        if self._D1 == 1:
            atten_D1_dB = 1
        if self._D0 == 1:
            atten_D0_dB = 0.5
        self._atten_dB = (
            atten_D5_dB
            + atten_D4_dB
            + atten_D3_dB
            + atten_D2_dB
            + atten_D1_dB
            + atten_D0_dB
        )
        self._atten_decimal = self._atten_dB * 2
        print(f"Attenuation for GPIO controlled DSA is {self._atten_dB} dB.")
        print("*** Attenuation Decimal = 2 * Attenuation (dB) ***")
        print(
            f"Attenuation Decimal (0~63) for GPIO controlled DSA is {self._atten_decimal}."
        )
        return self._atten_decimal

    @GPIO_attenuation.setter
    def GPIO_attenuation(self, value):
        if value < 0 or value >= 64:
            print("Please choose a valid value for Attenuation Decimal (0~63)")
            return
        self._atten_decimal = value
        self._atten_dB = value / 2
        print(
            f"Setting Attenuation Decimal (0~63) for GPIO controlled DSA to {self._atten_decimal}."
        )
        print("*** Attenuation (dB) = 0.5 * Attenuation Decimal ***")
        print(f"Setting attenuation for GPIO controlled DSA to {self._atten_dB} dB.")
        # Set D0 based on whether or not the Attenuation Decimal value is odd
        # (since odd Attenuation Decimal value / 2 gives an Attenuation dB value ending in 0.5)
        if value % 2 != 0:
            self._D0 = 1
        else:
            self._D0 = 0
        # Mask out each of the remaining bits from the Attenuation Decimal value to determine D5-D1
        self._D5 = (self._atten_decimal & (1 << 5)) >> 5
        self._D4 = (self._atten_decimal & (1 << 4)) >> 4
        self._D3 = (self._atten_decimal & (1 << 3)) >> 3
        self._D2 = (self._atten_decimal & (1 << 2)) >> 2
        self._D1 = (self._atten_decimal & (1 << 1)) >> 1
        self._set_iio_attr("voltage5", "raw", True, self._D5, self._ctrl)
        self._set_iio_attr("voltage4", "raw", True, self._D4, self._ctrl)
        self._set_iio_attr("voltage3", "raw", True, self._D3, self._ctrl)
        self._set_iio_attr("voltage2", "raw", True, self._D2, self._ctrl)
        self._set_iio_attr("voltage1", "raw", True, self._D1, self._ctrl)
        self._set_iio_attr("voltage0", "raw", True, self._D0, self._ctrl)
