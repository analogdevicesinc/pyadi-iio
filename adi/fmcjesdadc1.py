# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9250 import ad9250
from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import rx


class fmcjesdadc1(ad9250):

    """FMCJESDADC1 Four-Channel High Speed Data Acquisition FMC Board"""

    _split_cores = True
    _rx_channel_names = ["voltage0", "voltage1"]  # Recheck RX Channel Names
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):
        context_manager.__init__(self, uri, self._device_name)

        self._jesd = jesd(uri, username=username, password=password)
        self._rxadc = self._ctx.find_device("axi-ad9250-hpc-0")
        self._rxadc_chip_b = self._ctx.find_device("axi-ad9250-hpc-1")

        rx.__init__(self)

    @property
    def test_mode_chan0(self):
        """test_mode_chan0: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode_chan0.setter
    def test_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def test_mode_chan1(self):
        """test_mode_chan1: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage1", "test_mode", False)

    @test_mode_chan1.setter
    def test_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "test_mode", False, value, self._rxadc)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()
