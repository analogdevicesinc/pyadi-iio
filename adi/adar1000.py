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


class _dyn_device_property:
    """ Class descriptor for accessing device attributes """

    def __init__(self, attr, dev):
        self._dev = dev
        self._attr = attr

    def __get__(self, instance, owner):
        try:
            return instance._get_iio_dev_attr(self._attr, self._dev)
        except OSError:
            return instance._get_iio_dev_attr_str(self._attr, self._dev)

    def __set__(self, instance, value):
        if value in (True, False):
            value = int(value)
        instance._set_iio_dev_attr_str(self._attr, str(value), self._dev)


class _dyn_channel_property:
    """ Class descriptor for accessing channel attributes """

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
        try:
            instance._set_iio_attr_float(
                self._channel_name, self._attr, self._output, float(value), self._dev
            )
        except OSError:
            instance._set_iio_attr_int(
                self._channel_name, self._attr, self._output, int(value), self._dev
            )
        except ValueError:
            instance._set_iio_attr(
                self._channel_name, self._attr, self._output, str(value), self._dev
            )


class adar1000(attribute, context_manager):
    """ADAR1000 Beamformer

    parameters:
        uri: type=string
            URI of IIO context with ADAR1000(s)
        beams: type=string,list[string]
            String or list of strings identifying desired chip select
            option of ADAR1000. This is based on the jumper configuration
            if the EVAL-ADAR1000 is used. These strings are the labels
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
                    if (
                        "label" in dev.attrs
                        and dev.attrs["label"].value.lower() == beam.lower()
                    ):
                        self._ctrls.append(dev)
                        break
            if len(self._ctrls) != len(beams):
                raise Exception("Not all devices found: " + ",".join(beams))
        else:
            for dev in self._ctx.devices:
                if (
                    "label" in dev.attrs
                    and dev.attrs["label"].value.lower() == beams.lower()
                ):
                    self._ctrl = dev
            if not self._ctrl:
                raise Exception("No device found for BEAM: " + beams)

        if not isinstance(beams, list):
            beams = [None]
            self._ctrls = [self._ctrl]

        # Add all attributes for each beam as a class property
        for b, beam in enumerate(beams):
            dev = self._ctrls[b]

            # Only add the beam prefix to the property name if there are multiple devices
            attr_prefix = ""
            if len(beams) > 1:
                attr_prefix = f"{str(beam).lower()}_"

            # Add all the properties of interest for the device.
            for attr in dev.attrs:
                setattr(
                    type(self),
                    f"{attr_prefix}{attr}".lower(),
                    _dyn_device_property(attr, dev),
                )

            # For each device channel, add all the properties to the device
            for i, ch in enumerate(dev.channels):
                # Check to see if it's a temperature channel
                if "temp" in ch.id:
                    setattr(
                        type(self),
                        f"{attr_prefix}temp".lower(),
                        _dyn_channel_property("raw", dev, ch.id, ch.output),
                    )

                # If not, add all the channel's attributes
                else:
                    for attr in ch.attrs:
                        channel = int(ch.id.replace("voltage", "")) + 1

                        # Check to see if it's a detector read attribute
                        if attr.lower() == "raw":
                            setattr(
                                type(self),
                                f"{attr_prefix}ch{channel}_{ch.name.lower()}_detector".lower(),
                                _dyn_channel_property(attr, dev, ch.id, ch.output),
                            )

                        # Check to see if it's a sequencer attribute
                        elif any(s in attr.lower() for s in ("sequence", "bias_set")):
                            setattr(
                                type(self),
                                f"{attr_prefix}{ch.name.lower()}_{attr}".lower(),
                                _dyn_channel_property(attr, dev, ch.id, ch.output),
                            )

                        else:
                            setattr(
                                type(self),
                                f"{attr_prefix}ch{channel}_{ch.name.lower()}_{attr}".lower(),
                                _dyn_channel_property(attr, dev, ch.id, ch.output),
                            )
