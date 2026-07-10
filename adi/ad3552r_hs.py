# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import tx_chan_comp


class ad3552r_hs_channel(attribute):
    """AD3552R_HS channel"""

    def __init__(self, ctrl, channel_name, output):
        """Initialize an AD3552R_HS channel."""
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


class ad3552r_hs(tx_chan_comp):
    """AD3552R_HS DAC"""

    _complex_data = False
    _device_name = "AD3552R_HS"
    compatible_parts = [
        "ad3552r",
        "ad3551r",
        "ad3542r",
        "ad3541r",
    ]

    def __post_init__(self):
        """Populate the channel-wise output_bits list."""
        self.output_bits = []
        for ch in self._ctrl.channels:
            self.output_bits.append(ch.data_format.bits)

    def _channel_def(self, ctrl, name):
        output = ctrl.find_channel(name, True) is not None
        return ad3552r_hs_channel(ctrl, name, output)

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
