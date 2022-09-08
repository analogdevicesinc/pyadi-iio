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

# out_altvoltage0_channel_nco_enable
# out_altvoltage0_channel_nco_frequency
# out_altvoltage0_channel_nco_phase
# out_altvoltage0_channel_nco_scale
# out_altvoltage0_main_nco_enable
# out_altvoltage0_main_nco_frequency
# out_altvoltage0_main_nco_phase

class ad9173(attribute, context_manager):
    """AD9173 Microwave Wideband Synthesizer
    with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with AD9173
    """

    _device_name = "ad9173"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("AD9173 device not found")

    @property
    def channel0_nco_enable(self):
        """Get/Set the enable of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_enable", True, self._ctrl)

    @channel0_nco_enable.setter
    def channel0_nco_enable(self, value):
        """Get/Set the enable of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_enable", True, value, self._ctrl)

    @property
    def channel0_nco_frequency(self):
        """Get/Set the frequency of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_frequency", True, self._ctrl)

    @channel0_nco_frequency.setter
    def channel0_nco_frequency(self, value):
        """Get/Set the frequency of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_frequency", True, value, self._ctrl)

    @property
    def channel0_nco_scale(self):
        """Get/Set the scale of the channel0 NCO"""
        return self._get_iio_attr("altvoltage0", "channel_nco_scale", True, self._ctrl)

    @channel0_nco_scale.setter
    def channel0_nco_scale(self, value):
        """Get/Set the scale of the channel0 NCO"""
        self._set_iio_attr("altvoltage0", "channel_nco_scale", True, value, self._ctrl)

    @property
    def main0_nco_frequency(self):
        """Get/Set the frequency of the main0 NCO"""
        return self._get_iio_attr("altvoltage0", "main_nco_frequency", True, self._ctrl)

    @main0_nco_frequency.setter
    def main0_nco_frequency(self, value):
        """Get/Set the frequency of the main0 NCO"""
        self._set_iio_attr("altvoltage0", "main_nco_frequency", True, value, self._ctrl)

    @property
    def channel1_nco_enable(self):
        """Get/Set the enable of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_enable", True, self._ctrl)

    @channel1_nco_enable.setter
    def channel1_nco_enable(self, value):
        """Get/Set the enable of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_enable", True, value, self._ctrl)

    @property
    def channel1_nco_frequency(self):
        """Get/Set the frequency of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_frequency", True, self._ctrl)

    @channel1_nco_frequency.setter
    def channel1_nco_frequency(self, value):
        """Get/Set the frequency of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_frequency", True, value, self._ctrl)

    @property
    def channel1_nco_scale(self):
        """Get/Set the scale of the channel1 NCO"""
        return self._get_iio_attr("altvoltage1", "channel_nco_scale", True, self._ctrl)

    @channel1_nco_scale.setter
    def channel1_nco_scale(self, value):
        """Get/Set the scale of the channel1 NCO"""
        self._set_iio_attr("altvoltage1", "channel_nco_scale", True, value, self._ctrl)

    @property
    def main1_nco_frequency(self):
        """Get/Set the frequency of the main1 NCO"""
        return self._get_iio_attr("altvoltage1", "main_nco_frequency", True, self._ctrl)

    @main1_nco_frequency.setter
    def main1_nco_frequency(self, value):
        """Get/Set the frequency of the main1 NCO"""
        self._set_iio_attr("altvoltage1", "main_nco_frequency", True, value, self._ctrl)#

