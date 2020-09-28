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


class _dyn_property_float:
    """ Class descriptor for accessing individual attributes """

    def __init__(self, attr, dev, channel_name, output):
        self._dev = dev
        self._attr = attr
        self._channel_name = channel_name
        self._output = output

    def __get__(self, instance, owner):
        return instance._get_iio_attr(
            self._channel_name, self._attr, self._output, self._dev
        )

    def __set__(self, instance, value):
        instance._set_iio_attr_float(
            self._channel_name, self._attr, self._output, value, self._dev
        )


def _add_prop(classname, channelname, attr, i, inout, dev, beam_name=None):
    """ Add dynamic property """
    inoutstr = "rx" if inout else "tx"
    pn = inoutstr + str(i) + "_" + attr
    if beam_name:
        pn += "_" + beam_name.lower()

    setattr(
        classname,
        pn,
        _dyn_property_float(attr=attr, dev=dev, channel_name=channelname, output=inout),
    )


class adar1000(attribute, context_manager):
    """ ADAR1000 Beamformer

        parameters:
            uri: type=string
                URI of IIO context with ADAR100(s)
            beams: type=string,list[string]
                String or list of strings idenifying desired chip select
                option of ADAR100. This is based on the jumper configuration
                if the EVAL-ADAR100 is used. These strings are the labels
                coinciding with each chip select and are typically in the
                form BEAM0, BEAM1, BEAM2, BEAM3. Use a list when multiple
                are chips are cascaded together. Dynamic class properties
                will be created for each beam and signal path.
    """

    _device_name = ""
    _beam_channels = ["voltage0", "voltage1", "voltage2", "voltage3"]

    def __init__(self, uri="", beams="BEAM0"):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None
        self._ctrls = []

        if isinstance(beams, list):
            for beam in beams:
                for dev in self._ctx.devices:
                    if "label" in dev.attrs and dev.attrs["label"].value == beam:
                        self._ctrls.append(dev)
            if len(self._ctrls) == len(beams):
                raise Exception("Not all devices found: " + ",".join(beams))
        else:
            for dev in self._ctx.devices:
                if "label" in dev.attrs and dev.attrs["label"].value == beams:
                    self._ctrl = dev
            if not self._ctrl:
                raise Exception("No device found for BEAM: " + beams)

        # Dynamically add properties for accessing individual phases/gains
        if not isinstance(beams, list):
            beams = [None]
            self._ctrls = [self._ctrl]
        for b, beam in enumerate(beams):
            for i, chan_name in enumerate(self._beam_channels):
                dev = self._ctrls[b]
                _add_prop(type(self), chan_name, "phase", i, False, dev, beams[b])
                _add_prop(type(self), chan_name, "phase", i, True, dev, beams[b])
                _add_prop(
                    type(self), chan_name, "hardwaregain", i, False, dev, beams[b]
                )
                _add_prop(type(self), chan_name, "hardwaregain", i, True, dev, beams[b])

    @property
    def tx_hardwaregains(self):
        """tx_hardwaregains: Set all gains applied to TX path"""
        return [
            self._get_iio_attr(b, "hardwaregain", True, dev)
            for dev in self._ctrls
            for b in self._beam_channels
        ]

    @tx_hardwaregains.setter
    def tx_hardwaregains(self, values):
        self._set_iio_attr_float_multi_dev(
            self._beam_channels, "hardwaregain", True, values, self._ctrls
        )

    @property
    def rx_hardwaregains(self):
        """rx_hardwaregains: Set all gains applied to RX path"""
        return [
            self._get_iio_attr(b, "hardwaregain", False, dev)
            for dev in self._ctrls
            for b in self._beam_channels
        ]

    @rx_hardwaregains.setter
    def rx_hardwaregains(self, values):
        self._set_iio_attr_float_multi_dev(
            self._beam_channels, "hardwaregain", False, values, self._ctrls
        )

    @property
    def tx_phases(self):
        """tx_phases: Set all phases of TX path"""
        return [
            self._get_iio_attr(b, "phase", True, dev)
            for dev in self._ctrls
            for b in self._beam_channels
        ]

    @tx_phases.setter
    def tx_phases(self, values):
        self._set_iio_attr_float_multi_dev(
            self._beam_channels, "phase", True, values, self._ctrls
        )

    @property
    def rx_phases(self):
        """rx_phases: Set all phases of RX path"""
        return [
            self._get_iio_attr(b, "phase", False, dev)
            for dev in self._ctrls
            for b in self._beam_channels
        ]

    @rx_phases.setter
    def rx_phases(self, values):
        self._set_iio_attr_float_multi_dev(
            self._beam_channels, "phase", False, values, self._ctrls
        )
