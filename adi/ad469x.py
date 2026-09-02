# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad469x_channel(attribute):
    """AD469x base channel with attributes common to all parts."""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD469x channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD469x channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))


class ad4695_channel(ad469x_channel):
    """AD4695 channel with offset and calibration attributes (ad4695.c family)."""

    @property
    def offset(self):
        """AD469x channel offset."""
        return self._get_iio_attr_str(self.name, "offset", False)

    @offset.setter
    def offset(self, value):
        self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))

    @property
    def calibscale(self):
        """AD469x channel calibration scale."""
        return float(self._get_iio_attr_str(self.name, "calibscale", False))

    @calibscale.setter
    def calibscale(self, value):
        self._set_iio_attr(self.name, "calibscale", False, str(Decimal(value).real))

    @property
    def calibbias(self):
        """AD469x channel calibration bias."""
        return self._get_iio_attr(self.name, "calibbias", False)

    @calibbias.setter
    def calibbias(self, value):
        self._set_iio_attr(self.name, "calibbias", False, str(int(value)))


class ad4691_channel(ad469x_channel):
    """AD4691 channel with oversampling and sampling frequency (ad4691.c family)."""

    @property
    def scale(self):
        """AD4691 channel scale (device-level, shared by all channels)."""
        return float(self._get_iio_dev_attr_str("scale"))

    @scale.setter
    def scale(self, value):
        self._set_iio_dev_attr("scale", str(Decimal(value).real))

    @property
    def oversampling_ratio(self):
        """AD4691 channel oversampling ratio."""
        return self._get_iio_attr(self.name, "oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._set_iio_attr(self.name, "oversampling_ratio", False, str(int(value)))

    @property
    def oversampling_ratio_available(self):
        """List of available oversampling ratios."""
        return self._get_iio_attr_str(self.name, "oversampling_ratio_available", False)

    @property
    def sampling_frequency(self):
        """AD4691 channel sampling frequency in Hz."""
        return self._get_iio_attr(self.name, "sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr(self.name, "sampling_frequency", False, str(int(value)))


_AD4691_PARTS = {"ad4691", "ad4692", "ad4693", "ad4694"}


class ad469x(rx_chan_comp):
    """AD469x ADC.

    Supports the ad4695.c Linux driver family (ad4695/96/97/98) and the
    ad4691.c Linux driver family (ad4691/92/93/94).
    """

    channel = []  # type: ignore
    compatible_parts = [
        "ad4691",
        "ad4692",
        "ad4693",
        "ad4694",
        "ad4695",
        "ad4696",
        "ad4697",
        "ad4698",
    ]
    _device_name = ""
    _complex_data = False
    _channel_def = ad469x_channel

    def __init__(self, uri="", device_name=""):
        if device_name in _AD4691_PARTS:
            self._channel_def = ad4691_channel
        else:
            self._channel_def = ad4695_channel
        super().__init__(uri=uri, device_name=device_name)

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
