# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import rx
from adi.sync_start import sync_start


class ad9250(rx, context_manager, sync_start):

    """ AD9250 High-Speed ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad9250-hpc")
        self._jesd = jesd(uri, username=username, password=password)

        rx.__init__(self)

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()
