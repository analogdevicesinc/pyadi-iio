# Copyright (C) 2022-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4080(rx, context_manager):

    """ AD4080 ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = "ad4080"

    def __init__(self, uri=""):

        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("ad4080")
        self._ctrl = self._ctx.find_device("ad4080")

        rx.__init__(self)

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr_str("voltage0", "test_mode", False)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr_str("voltage0", "test_mode", False, value, self._rxadc)

    @property
    def test_mode_available(self):
        """test_mode_available: Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr_str("voltage0", "test_mode_available", False)

    @property
    def scale(self):
        """scale: Scale value"""
        return self._get_iio_attr("voltage0", "scale", False)

    @property
    def scale_available(self):
        """scale_avaliable: Available scale value"""
        return self._get_iio_attr("voltage0", "scale_available", False)

    @property
    def sampling_frequency(self):
        """sampling_frequency: Sampling frequency value"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False)
