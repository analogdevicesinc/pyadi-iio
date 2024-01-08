# Copyright (C) 2021-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

from adi.context_manager import context_manager
from adi.dma_helpers import _channel
from adi.rx_tx import rx_def


class ad760x(rx_def, context_manager):
    """Common class for the AD760x ADCs"""
    _complex_data = False
    _device_name = ""
    _enabled_channel_components = True

    @property
    def scale_available(self):
        """Provides all available scale settings for the ADC channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)

    @property
    def range_available(self):
        """Provides all available range settings for the ADC channels"""
        return self._get_iio_attr(self.channel[0].name, "range_available", False)

    @property
    def oversampling_ratio(self):
        """Oversampling_ratio"""
        return self._get_iio_attr(self.name, "oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._get_iio_attr(self.name, "oversampling_ratio", False, value)

    @property
    def oversampling_ratio_available(self):
        """Channel oversampling_ratio_available"""
        return self._get_iio_attr(self.name, "oversampling_ratio_available", False)


class ad7605_4(ad760x):
    """ AD7605-4 ADC """
    _control_device_name = "ad7605-4"
    _rx_data_device_name = "ad7605-4"
    _rx_channel_names = [f"voltage{i}" for i in range(4)]


class ad7606_4(ad7605_4):
    """ AD7606-4 ADC """
    _control_device_name = "ad7606-4"
    _rx_data_device_name = "ad7606-4"


class ad7606_6(ad760x):
    """ AD7606-6 ADC """
    _control_device_name = "ad7606-6"
    _rx_data_device_name = "ad7606-6"
    _rx_channel_names = [f"voltage{i}" for i in range(6)]


class ad7606_8(ad760x):
    """ AD7606-8 ADC """
    _control_device_name = "ad7606-8"
    _rx_data_device_name = "ad7606-8"
    _rx_channel_names = [f"voltage{i}" for i in range(6)]


class ad7606b(ad760x):
    """ AD7606B ADC """
    _control_device_name = "ad7606b"
    _rx_data_device_name = "ad7606b"
    _rx_channel_names = [f"voltage{i}" for i in range(6)]


class ad7606c_16(ad760x):
    """ AD7606C-16 ADC """
    _control_device_name = "ad7606c-16"
    _rx_data_device_name = "ad7606c-16"
    _rx_channel_names = [f"voltage{i}" for i in range(8)]


class ad7606c_18(ad760x):
    """ AD7606C-18 ADC """
    _control_device_name = "ad7606c-18"
    _rx_data_device_name = "ad7606c-18"
    _rx_channel_names = [f"voltage{i}" for i in range(8)]
