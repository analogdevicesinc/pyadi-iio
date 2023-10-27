"""Common methods for DMA channels."""
from .attribute import attribute

from decimal import Decimal
from iio import Device


class dma_channel(attribute):
    """ADC channel"""

    def __init__(self, ctrl: Device, channel_name: str):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """Channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """Channel scale (gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    @property
    def offset(self):
        """Channel offset (bias)"""
        return self._get_iio_attr(self.name, "offset", False)

    @offset.setter
    def offset(self, value):
        self._get_iio_attr(self.name, "offset", False, value)