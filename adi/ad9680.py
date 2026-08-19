# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.device_base import rx_def
from adi.sync_start import sync_start


class ad9680(rx_def, sync_start):
    """ AD9680 High-Speed ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""
    _control_device_name = None
    _rx_data_device_name = "axi-ad9680-hpc"
    compatible_parts = ["axi-ad9680-hpc"]

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)
