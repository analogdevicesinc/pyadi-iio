# Copyright (C) 2022-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4080(rx, context_manager):

    """ AD4080 ADC """

    _compatible_parts = ["ad4080"]
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""

    def __init__(self, uri="", device_name="ad4080"):

        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        if device_name not in self._compatible_parts:
            raise Exception(
                "Not a compatible device: "
                + str(device_name)
                + ". Please select from "
                + str(self.self._compatible_parts)
            )
        else:
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)

        rx.__init__(self)

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
        return self._get_iio_dev_attr("sampling_frequency")

    @property
    def sinc_dec_rate_available(self):
        """"""
        return self._get_iio_dev_attr("sinc_dec_rate_available", False)

    @property
    def sinc_dec_rate(self):
        """"""
        return self._get_iio_dev_attr("sinc_dec_rate", False)

    @sinc_dec_rate.setter
    def sinc_dec_rate(self, value):
        self._set_iio_dev_attr("sinc_dec_rate", value)

    @property
    def filter_sel_available(self):
        """"""
        return self._get_iio_dev_attr_str("filter_sel_available", False)

    @property
    def filter_sel(self):
        """"""
        return self._get_iio_dev_attr_str("filter_sel", False)

    @filter_sel.setter
    def filter_sel(self, value):
        self._set_iio_dev_attr_str("filter_sel", value)
