# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad7799_channel(attribute):
    """AD7799 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def value(self):
        """AD7799 channel mV value"""
        return self._get_iio_attr(self.name, "volts", False, self._ctrl)


class ad7799(rx_chan_comp):
    """ AD7799 ADC """

    compatible_parts = ["AD7799"]
    _rx_channel_names = ["channel0", "channel1", "channel2"]
    _complex_data = False
    _channel_def = ad7799_channel
    _control_device_name = "AD7799"
    _rx_data_device_name = "AD7799"

    @property
    def gain(self):
        """Get gain of the AD7799"""
        return self._get_iio_dev_attr_str("gain", self._rxadc)

    @gain.setter
    def gain(self, value):
        """Sets gain of the AD7799"""
        self._set_iio_dev_attr_str("gain", value, self._rxadc)
