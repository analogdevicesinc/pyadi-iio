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

import re
import numpy as np
from typing import Dict, List

from adi.context_manager import context_manager
from adi.rx_tx import rx

class ad4696(rx, context_manager):
    """AD4696 Easy Driver Multiplexed SAR ADC"""

    _rx_output_type = "SI"
    _rx_unbuffered_data = True
    _complex_data = False
    _rx_channel_names: List[str] = []

    _rx_data_si_type = np.double
    
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device(device_name)
        if not self._rxadc:
            raise Exception(f"Cannot find device with name '{device_name}'")
        self._ctrl = self._rxadc

        for ch in self._rxadc.channels:
            self._rx_channel_names.append(ch._id)

        # Sort channel names alphabetically
        self._rx_channel_names.sort(key=self._sort_key)

        rx.__init__(self)
        self.rx_buffer_size = 1

    def _sort_key(self, ch_names):
        return list(map(int, re.findall(r'\d+', ch_names)))[0]

    def rx(self):
        """Overridden rx method to properly compute and format capture data"""
        adc_data = super().rx()

        # create dictionary of channels to the value
        capture_dict = {}

        for idx, ch in enumerate(self._rx_channel_names):
            # scale is off by 1000, compensate here
            adc_data[idx] /= 1000.0
            capture_dict[ch] = adc_data[idx][0]

        return capture_dict

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._rxadc)
        return self._get_iio_debug_attr_str("direct_reg_access", self._rxadc)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._rxadc)

