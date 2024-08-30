"""This module contains shared functionality for ADI devices."""
from decimal import Decimal

from adi.attribute import attribute

class rx_buffered_channel(attribute):
    """RX buffered channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """Channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)
    
    @property
    def millivolts(self):
        """Channel value in millivolts"""
        return (self.raw + self.offset) * self.scale

    @property
    def offset(self):
        """Channel offset or bias"""
        return self._get_iio_attr_str(self.name, "offset", False)

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))

    @property
    def scale(self):
        """Channel scale or gain"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

