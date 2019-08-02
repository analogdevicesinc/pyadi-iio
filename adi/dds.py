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
import numpy as np


class dds(attribute):
    """ DDS Signal generators: Each reference design contains two DDSs per channel.
        this allows for two complex tones to be generated per complex channel.
    """

    dds_frequencies = []
    dds_scales = []
    dds_phases = []
    dds_enabled = []

    def __init__(self):
        self.dds_frequencies = np.zeros(self.num_tx_channels * 2)
        self.dds_scales = np.zeros(self.num_tx_channels * 2)
        self.dds_phases = np.zeros(self.num_tx_channels * 2)
        self.dds_enabled = np.zeros(self.num_tx_channels * 2, dtype=bool)

    def update_dds(self, attr, value):
        indx = 0
        for chan in self.txdac.channels:
            if not chan.name:
                continue
            if attr == "raw":
                chan.attrs[attr].value = str(int(value[indx]))
            else:
                chan.attrs[attr].value = str(value[indx])
            indx = indx + 1

    def read_dds(self, attr):
        values = []
        indx = 0
        for chan in self.txdac.channels:
            if not chan.name:
                continue
            values.append(chan.attrs[attr].value)
            indx = indx + 1
        return values

    def disable_dds(self):
        self.dds_enabled = np.zeros(self.num_tx_channels * 2, dtype=bool)

    @property
    def dds_frequencies(self):
        """ Frequencies of DDSs in Hz"""
        return self.read_dds("frequency")

    @dds_frequencies.setter
    def dds_frequencies(self, value):
        self.update_dds("frequency", value)

    @property
    def dds_scales(self):
        """ Scale of DDS signal generators
            Ranges [0,1]
        """
        return self.read_dds("scale")

    @dds_scales.setter
    def dds_scales(self, value):
        self.update_dds("scale", value)

    @property
    def dds_phases(self):
        """ Phases of DDS signal generators.
            Range in millidegrees [0,360000]
        """
        return self.read_dds("phase")

    @dds_scales.setter
    def dds_phases(self, value):
        self.update_dds("phase", value)

    @property
    def dds_enabled(self):
        """ DDS generator enable state """
        return self.read_dds("raw")

    @dds_enabled.setter
    def dds_enabled(self, value):
        self.update_dds("raw", value)
