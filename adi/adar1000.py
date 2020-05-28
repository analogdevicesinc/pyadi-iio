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

from adi.attribute import attribute
from adi.context_manager import context_manager


def add_prop(classname, channelname, attr, i, inout):
    def fget(self):
        self._get_iio_attr(channelname + str(i), attr, inout)

    def fset(self, value):
        self._set_iio_attr("voltage" + str(i), attr, inout, value)

    doc = "Phase of channel " + str(i)
    inoutstr = "rx" if inout else "tx"
    pn = inoutstr + str(i) + "_" + attr
    setattr(
        classname, pn, property(fget=fget, fset=fset, doc=doc),
    )


class adar1000(attribute, context_manager):
    """ ADAR1000 Beamformer """

    _device_name = ""
    _beam_channels = ["voltage0", "voltage1", "voltage2", "voltage3"]

    def __init__(self, uri="", beam="BEAM0"):
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None
        for dev in self._ctx.devices:
            if dev.attrs["label"].value == beam:
                self._ctrl = dev
        if not self._ctrl:
            raise Exception("No device found for BEAM: " + beam)
        for i in range(4):
            add_prop(type(self), "voltage", "phase", i, False)
            add_prop(type(self), "voltage", "phase", i, True)
            add_prop(type(self), "voltage", "hardwaregain", i, False)
            add_prop(type(self), "voltage", "hardwaregain", i, True)

    @property
    def tx_hardwaregains(self):
        """tx_hardwaregains: Gains applied to TX path"""
        bs = self._beam_channels
        return [self._get_iio_attr(b, "hardwaregain", True) for b in bs]

    @tx_hardwaregains.setter
    def tx_hardwaregains(self, value):
        for i, v in enumerate(value):
            self._set_iio_attr_float(self._beam_channels[i], "hardwaregain", True, v)

    @property
    def rx_hardwaregains(self):
        """rx_hardwaregains: Gains applied to RX path"""
        bs = self._beam_channels
        return [self._get_iio_attr(b, "hardwaregain", False) for b in bs]

    @rx_hardwaregains.setter
    def rx_hardwaregains(self, value):
        for i, v in enumerate(value):
            self._set_iio_attr_float(self._beam_channels[i], "hardwaregain", False, v)

    @property
    def tx_phases(self):
        """tx_phases: Phases of TX path"""
        bs = self._beam_channels
        return [self._get_iio_attr(b, "phase", True) for b in bs]

    @tx_phases.setter
    def tx_phases(self, value):
        for i, v in enumerate(value):
            self._set_iio_attr_float(self._beam_channels[i], "phase", True, v)

    @property
    def rx_phases(self):
        """rx_phases: Phases of RX path"""
        bs = self._beam_channels
        return [self._get_iio_attr(b, "phase", False) for b in bs]

    @rx_phases.setter
    def rx_phases(self, value):
        for i, v in enumerate(value):
            self._set_iio_attr_float(self._beam_channels[i], "phase", False, v)
