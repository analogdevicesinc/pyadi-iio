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


class _dyn_property:
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
        instance._set_iio_attr_int(
            self._channel_name, self._attr, self._output, int(value), self._dev
        )


class one_bit_adc_dac(attribute, context_manager):
    """One bit ADC/DAC (GPIO). This driver will create a handle for the
        GPIO device as well as properties for each GPIO pin it accesses.
        Each GPIO pin name will be lowercase and of the format:
        "gpio_{pin name}"

    parameters:
        uri: type=string
            URI of IIO context with GPIO pins
        name: type=string
            String identifying the device by name from the device tree.
            Dynamic class properties will be created for each channel.
    """

    _device_name = ""

    def __init__(self, uri="", name="one-bit-adc-dac"):

        try:
            context_manager.__init__(self, uri, self._device_name)
        except Exception:
            raise Exception(f"No device found for {name}")

        self._ctrl = None

        for dev in self._ctx.devices:
            if "label" in dev.attrs and dev.attrs["label"].value == name:
                self._ctrl = dev
                break
            else:
                if dev.name == name:
                    self._ctrl = dev
                    break

        if not self._ctrl:
            raise Exception(f"No device found for {name}")

        for chan in self._ctrl.channels:
            setattr(
                type(self),
                f"gpio_{chan.attrs['label'].value.lower()}",
                _dyn_property(
                    "raw", dev=self._ctrl, channel_name=chan.id, output=chan.output
                ),
            )
