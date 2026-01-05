# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad3552r_hs(tx, context_manager):
    """AD3552R_HS DAC"""

    _complex_data = False
    _device_name = "AD3552R_HS"

    def __init__(self, uri="", device_name=""):
        """ Constructor for AD3552R_HS driver class """

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad3552r",
            "ad3551r",
            "ad3542r",
            "ad3541r",
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

    @property
    def input_source(self):
        """Input source of the DAC"""
        return self._get_iio_dev_attr_str("input_source", self._txdac)

    @input_source.setter
    def input_source(self, value):
        self._set_iio_dev_attr_str("input_source", value, self._txdac)

    @property
    def stream_status(self):
        """Stream status of the DAC"""
        return self._get_iio_dev_attr_str("stream_status", self._txdac)

    @stream_status.setter
    def stream_status(self, value):
        self._set_iio_dev_attr_str("stream_status", value, self._txdac)

    @property
    def output_range(self):
        """Stream status of the DAC"""
        return self._get_iio_dev_attr_str("output_range", self._txdac)

    @output_range.setter
    def output_range(self, value):
        self._set_iio_dev_attr_str("output_range", value, self._txdac)

    class _channel(attribute):
        """AD3552R_HS channel"""

        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        def sample_rate(self):
            """Sample rate of the DAC"""
            return self._get_iio_attr(self.name, "sampling_frequency", True)

        @sample_rate.setter
        def sample_rate(self, value):
            self._set_iio_attr(self.name, "sampling_frequency", True, value)

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
            self._set_iio_attr(self.name, "scale", True, str(Decimal(value).real))
