# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad4080_channel(attribute):
    """AD4080 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def scale(self):
        """Get Scale value"""
        return self._get_iio_attr("voltage0", "scale", False)


class ad4080(rx_chan_comp):
    """AD4080 ADC"""

    channel = []  # type: ignore
    compatible_parts = [
        "ad4080",
        "ad4081",
        "ad4083",
        "ad4084",
        "ad4086",
        "ad4087",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad4080_channel

    @property
    def sampling_frequency(self):
        """Get Sampling frequency value"""
        return self._get_iio_dev_attr("sampling_frequency", False)

    @property
    def oversampling_ratio_available(self):
        """Get the oversampling ratio available values"""
        return self._get_iio_dev_attr("oversampling_ratio_available", False)

    @property
    def oversampling_ratio(self):
        """Get the oversampling ratio value"""
        return self._get_iio_dev_attr("oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        """Set the oversampling ratio value"""
        self._set_iio_dev_attr("oversampling_ratio", value)

    @property
    def filter_type_available(self):
        """Get the filter type available values"""
        return self._get_iio_dev_attr_str("filter_type_available", False)

    @property
    def filter_type(self):
        """Get the filter type value"""
        return self._get_iio_dev_attr_str("filter_type", False)

    @filter_type.setter
    def filter_type(self, value):
        """Set the filter type value"""
        self._set_iio_dev_attr_str("filter_type", value)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
