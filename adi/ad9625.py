# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import rx
from adi.sync_start import sync_start


class ad9625(rx, context_manager, sync_start):

    """ AD9625 High-Speed ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):

        context_manager.__init__(self, uri, self._device_name)

        self._jesd = jesd(uri, username=username, password=password)
        self._rxadc = self._ctx.find_device("axi-ad9625-hpc")

        rx.__init__(self)

    @property
    def rx_sample_rate(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._rxadc)

    @property
    def scale(self):
        """scale: AD9625 Gain"""
        return float(self._get_iio_attr("voltage0", "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr("voltage0", "scale", False, str(Decimal(value).real))

    @property
    def scale_available(self):
        """Provides all available scale settings for the AD9625"""
        return self._get_iio_attr("voltage0", "scale_available", False)

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off, midscale_short, pos_fullscale, neg_fullscale, checkerboard,
        pn_long, pn_short, one_zero_toggle, user, ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()
