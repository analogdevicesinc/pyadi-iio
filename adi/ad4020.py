# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad4020_channel(attribute):
    """AD4020 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD4020 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD4020 channel scale"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))


class ad4000_channel(ad4020_channel):
    """AD4000 channel"""

    @property
    def sampling_frequency(self):
        """Get and set the sampling frequency."""
        return self._get_iio_attr(self.name, "sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set the sampling frequency."""
        self._set_iio_attr(self.name, "sampling_frequency", False, value)


class __ad40xx_sr(object):
    """AD40xx sample rate control mixin class"""

    @property
    def sampling_frequency(self):
        """Get and set the sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set the sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", value)


class ad4020(rx_chan_comp):
    """AD4020 device"""

    channel = []  # type: ignore
    compatible_parts = ["ad4020", "ad4021", "ad4022"]
    _device_name = ""
    _rx_data_type = np.int32
    _complex_data = False
    _channel_def = ad4020_channel


class ad4000(ad4020):
    """AD4000 device"""

    compatible_parts = ["ad4000", "ad4004", "ad4008"]
    _rx_data_type = np.uint16
    _channel_def = ad4000_channel

    def __init__(self, uri="", device_name="ad4000"):
        super().__init__(uri, device_name)


class ad4001(ad4020, __ad40xx_sr):
    """AD4001 device"""

    compatible_parts = ["ad4001", "ad4005"]
    _rx_data_type = np.int16

    def __init__(self, uri="", device_name="ad4001"):
        super().__init__(uri, device_name)


class ad4002(ad4020):
    """AD4002 device"""

    compatible_parts = ["ad4002", "ad4006", "ad4010"]
    _rx_data_type = np.uint32
    _channel_def = ad4000_channel

    def __init__(self, uri="", device_name="ad4002"):
        super().__init__(uri, device_name)


class ad4003(ad4020, __ad40xx_sr):
    """AD4003 device"""

    compatible_parts = ["ad4003", "ad4007", "ad4011"]
    _rx_data_type = np.int32

    def __init__(self, uri="", device_name="ad4003"):
        super().__init__(uri, device_name)
