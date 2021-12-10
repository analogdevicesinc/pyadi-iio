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

from typing import List

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad9083(rx, context_manager):
    """AD9083 High-Speed Multi-channel ADC"""

    _complex_data = False
    _rx_channel_names: List[str] = []

    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad9083-rx-hpc")
        if not self._rxadc:
            raise Exception("Cannot find device axi-ad9083-rx-hpc")

        for ch in self._rxadc.channels:
            if ch.scan_element and not ch.output:
                self._rx_channel_names.append(ch._id)

        for name in self._rx_channel_names:
            if "_i" in name or "_q" in name:
                self._complex_data = True

        rx.__init__(self)

    @property
    def rx_sample_rate(self):
        """rx_sampling_frequency: Sample rate after decimation"""
        return self._get_iio_attr(
            "voltage0_i", "sampling_frequency", False, self._rxadc
        )

    @property
    def nco0_frequency(self):
        """nco0_frequency: Get/Set NCO0 frequency"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._rxadc)

    @nco0_frequency.setter
    def nco0_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "frequency", True, int(value), self._rxadc
        )

    @property
    def nco1_frequency(self):
        """nco0_frequency: Get/Set NCO1 frequency"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._rxadc)

    @nco1_frequency.setter
    def nco1_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "frequency", True, int(value), self._rxadc
        )

    @property
    def nco2_frequency(self):
        """nco0_frequency: Get/Set NCO2 frequency"""
        return self._get_iio_attr("altvoltage2", "frequency", True, self._rxadc)

    @nco2_frequency.setter
    def nco2_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "frequency", True, int(value), self._rxadc
        )

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._rxadc)
        return self._get_iio_debug_attr_str("direct_reg_access", self._rxadc)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._rxadc)
