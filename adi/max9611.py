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

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class max9611(rx, context_manager):
    """AD611 Current-sense Amplifier with ADC"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)
        compatible_parts = ["max9611", "max9612"]
        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        # Dynamically get channels after the index
        for ch in self._ctrl.channels:
            name = ch._id

            if name == "voltage0":
                setattr(self, name, self._channel_voltage_sense(self._ctrl, name))
            elif name == "voltage1":
                setattr(self, name, self._channel_voltage_input(self._ctrl, name))
                self._rx_channel_names.append(name)
            elif name == "power":
                setattr(self, name, self._channel_power(self._ctrl, name))
            elif name == "current":
                setattr(self, name, self._channel_current(self._ctrl, name))
            elif name == "temp":
                setattr(self, name, self._channel_temp(self._ctrl, name))
                self._rx_channel_names.append(name)

        self._rx_unbuffered_data = True

        rx.__init__(self)

    class _channel_voltage_sense(attribute):
        """MAX9611 Voltage Sense Channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def input(self):
            """MAX9611 Voltage Sense Channel input value."""
            return self._get_iio_attr(self.name, "input", False)

    class _channel_voltage_input(attribute):
        """MAX9611 Voltage Input Channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """MAX9611 Voltage Input Channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """MAX9611 Voltage Input Channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @property
        def offset(self):
            """Voltage Input Channel offset."""
            return float(self._get_iio_attr_str(self.name, "offset", False))

    class _channel_power(attribute):
        """MAX9611 Power Channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def input(self):
            """MAX9611 Power Channel input value."""
            return self._get_iio_attr(self.name, "input", False)

        @property
        def shunt_resistor(self):
            """MAX9611 Power Channel shunt resistor."""
            return float(self._get_iio_attr_str(self.name, "shunt_resistor", False))

    class _channel_current(attribute):
        """MAX9611 Current Channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def input(self):
            """MAX9611 Current Channel input value."""
            return self._get_iio_attr(self.name, "input", False)

        @property
        def shunt_resistor(self):
            """MAX9611 Current Channel shunt resistor."""
            return float(self._get_iio_attr_str(self.name, "shunt_resistor", False))

    class _channel_temp(attribute):
        """MAX9611 Temperature Channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """MAX9611 Temperature Channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """MAX9611 Temperature Channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))
