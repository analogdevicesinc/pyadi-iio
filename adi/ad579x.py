# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import tx_chan_comp


class ad579x_channel(attribute):
    """AD579x channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD579x channel raw value"""
        return self._get_iio_attr(self.name, "raw", True)

    @raw.setter
    def raw(self, value):
        self._set_iio_attr(self.name, "raw", True, str(int(value)))

    @property
    def offset(self):
        """AD579x channel offset"""
        return self._get_iio_attr(self.name, "offset", True)

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", True, str(Decimal(value).real))

    @property
    def scale(self):
        """AD579x channel scale"""
        return self._get_iio_attr(self.name, "scale", True)

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", True, str(Decimal(value).real))

    @property
    def powerdown(self):
        """AD579x powerdown config"""
        return self._get_iio_attr_str(self.name, "powerdown", True)

    @powerdown.setter
    def powerdown(self, value):
        self._set_iio_attr(self.name, "powerdown", True, value)

    @property
    def powerdown_available(self):
        """AD579x powedown available"""
        return self._get_iio_attr_str(self.name, "powerdown_available", True)


class ad579x(tx_chan_comp):
    """ AD579x DAC """

    channel = []  # type: ignore
    compatible_parts = [
        "ad5780",
        "ad5781",
        "ad5790",
        "ad5791",
        "ad5760",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad579x_channel

    def __post_init__(self):
        """Populate output_bits list"""
        self.output_bits = []
        for ch in self._ctrl.channels:
            self.output_bits.append(ch.data_format.bits)

    @property
    def powerdown_mode(self):
        """Ad579x powerdown_mode config"""
        return self._get_iio_dev_attr_str("powerdown_mode")

    @powerdown_mode.setter
    def powerdown_mode(self, value):
        self._set_iio_dev_attr_str("powerdown_mode", value)

    @property
    def powerdown_mode_available(self):
        """AD579x powedown mode available"""
        return self._get_iio_dev_attr_str("powerdown_mode_available")

    @property
    def sampling_frequency(self):
        """AD579x sampling frequency config"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)
