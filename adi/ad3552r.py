# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad3552r(tx, context_manager):
    """ AD3552R DAC """

    _complex_data = False
    _device_name = "AD3552R"

    def __init__(self, uri="", device_name=""):
        """ Constructor for AD3552R driver class """

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad3552r",
            "ad3542r",
        ]

        self._ctrl = None
        self._txdac = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(
                    f"Not a compatible device: {device_name}. Supported device names "
                    f"are: {','.join(compatible_parts)}"
                )

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._txdac = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._txdac:
            raise Exception("Error in selecting matching device")

        self.output_bits = []
        self.channel = []
        self._tx_channel_names = []
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            self.output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name, output))
            if output is True:
                setattr(self, name, self._channel(self._ctrl, name, output))

        tx.__init__(self)

    class _channel(attribute):
        """AD3552R channel"""

        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        def raw(self):
            """Get channel raw value
                DAC code in the range 0-65535"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            """Set channel raw value"""
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """Get channel offset"""
            return self._get_iio_attr_str(self.name, "offset", True)

        @offset.setter
        def offset(self, value):
            """Set channel offset"""
            self._set_iio_attr(self.name, "offset", True, str(Decimal(value).real))

        @property
        def scale(self):
            """Get channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", True))

        @scale.setter
        def scale(self, value):
            """Set channel scale"""
            self._set_iio_attr(self.name, "scale", True, str(Decimal(value).real))
