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


class admv8818(attribute, context_manager):
    """ADMV8818 2 GHz to 18 GHz, Digitally Tunable, High-Pass and Low-Pass Filter

    parameters:
        uri: type=string
            URI of IIO context with ADMV8818
    """

    _device_name = "admv8818"

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._device_name = device_name
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADMV8818 device not found")

    @property
    def low_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_low_pass_3db_frequency", True, self._ctrl
        )

    @low_pass_3db_frequency.setter
    def low_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0", "filter_low_pass_3db_frequency", True, int(value), self._ctrl
        )

    @property
    def high_pass_3db_frequency(self):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_high_pass_3db_frequency", True, self._ctrl
        )

    @high_pass_3db_frequency.setter
    def high_pass_3db_frequency(self, value):
        """Get/Set the Low Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_high_pass_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_bandwidth_3db_frequency(self):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_bandwidth_3db_frequency", True, self._ctrl
        )

    @band_pass_bandwidth_3db_frequency.setter
    def band_pass_bandwidth_3db_frequency(self, value):
        """Get/Set the Band Pass 3dB Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_bandwidth_3db_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def band_pass_center_frequency(self):
        """Get/Set the Band Pass Center Frequency in MHz"""
        return self._get_iio_attr(
            "altvoltage0", "filter_band_pass_center_frequency", True, self._ctrl
        )

    @band_pass_center_frequency.setter
    def band_pass_center_frequency(self, value):
        """Get/Set the Band Pass Center Frequency in MHz"""
        self._set_iio_attr_int(
            "altvoltage0",
            "filter_band_pass_center_frequency",
            True,
            int(value),
            self._ctrl,
        )

    @property
    def mode_available(self):
        """Get available modes"""
        return self._get_iio_attr_str("altvoltage0", "mode_available", True, self._ctrl)

    @property
    def mode(self):
        """Get/Set mode"""
        return self._get_iio_attr_str("altvoltage0", "mode", True, self._ctrl)

    @mode.setter
    def mode(self, value):
        """Get/Set mode"""
        self._set_iio_attr("altvoltage0", "mode", True, value, self._ctrl)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
