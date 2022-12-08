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
#        from this software without specific prior written permission.
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


from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad5592r(context_manager):
    """AD5592R ADC/DAC"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad5592r",
            "ad5593r",
        ]

        self.ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Selecting the device matching device_name AD559XR family as working device.
        for device in self._ctx.devices:
            if device.name in device_name:
                self._ctrl = device
                break

        # Dynamically get channels after the index
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            if name == "temp":
                setattr(self, name, self._channel(self._ctrl, name, output))
            else:
                if output is True:
                    setattr(
                        self, name + "_dac", self._channel(self._ctrl, name, output)
                    )
                else:
                    setattr(
                        self, name + "_adc", self._channel(self._ctrl, name, output)
                    )

    class _channel(attribute):
        """AD5592R Input/Output Voltage Channels"""

        # AD559XR voltage channel
        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        # AD559XR channel raw value
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self._output)

        @property
        # AD559XR channel scale (gain)
        def scale(self):
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @property
        # AD559XR channel temp offset value
        def offset(self):
            return self._get_iio_attr(self.name, "offset", self._output)

        @raw.setter
        def raw(self, value):
            if self._output is True:
                self._set_iio_attr(self.name, "raw", self._output, value)

        @scale.setter
        def scale(self, value):
            scale_available = self._get_iio_attr(
                self.name, "scale_available", self._output
            )
            for scale_available_0 in scale_available:
                if scale_available_0 == value:
                    self._set_iio_attr(
                        self.name,
                        "scale",
                        self._output,
                        value,  # str(Decimal(value).real) # Why do some device classes use Decimal??
                    )

        @property
        def scale_available(self):
            return self._get_iio_attr(self.name, "scale_available", self._output)
