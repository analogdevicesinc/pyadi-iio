# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.device_base import rx_def


class ad9265(rx_def):

    """AD9265 High-Speed ADC"""

    compatible_parts = ["axi-ad9265-core-lpc"]
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _rx_data_device_name = "axi-ad9265-core-lpc"
    _control_device_name = "axi-ad9265-core-lpc"

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard
        pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr_str("voltage0", "test_mode", False, self._rxadc)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)
