# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.device_base import rx_def


class ad9213(rx_def):
    """AD9213 High-Speed ADC."""

    compatible_parts = ["ad9213"]
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _rx_data_device_name = "ad9213"
    _control_device_name = "ad9213"

    @property
    def sampling_frequency(self):
        """sampling_frequency: Sample rate of the ADC in Hz."""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._rxadc)

    def register_read(self, reg):
        """Direct Register Access via debugfs."""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def register_write(self, reg, value):
        """Direct Register Access via debugfs."""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
