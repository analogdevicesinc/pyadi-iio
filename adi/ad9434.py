# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad9434(rx, context_manager):

    """AD9434 High-Speed ADC"""

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad9434-core-lpc")

        rx.__init__(self)

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard
        pn_long pn_short one_zero_toggle user"""
        return self._get_iio_attr_str("voltage0", "test_mode", False, self._rxadc)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)
