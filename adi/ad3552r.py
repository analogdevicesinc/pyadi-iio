# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import tx_chan_comp


class ad3552r_channel(attribute):
    """AD3552R channel"""

    def __init__(self, ctrl, channel_name, output=None):
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


class ad3552r(tx_chan_comp):
    """ AD3552R DAC """

    compatible_parts = ["ad3552r", "ad3542r"]
    _complex_data = False
    _channel_def = ad3552r_channel
    _control_device_name = ""
    _tx_data_device_name = ""

    def __post_init__(self):
        """Set up output_bits list and named channel access."""
        self.output_bits = []
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            self.output_bits.append(ch.data_format.bits)
            if output is True:
                # Add named channel access for output channels
                for i, chan in enumerate(self.channel):
                    if chan.name == name:
                        setattr(self, name, self.channel[i])
                        break
