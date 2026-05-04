# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad469x_channel(attribute):
    """AD469x channel

    Supports both the ad4695.c family (ad4695/96/97/98) and the ad4691.c
    family (ad4691/92/93/94). Attributes that are not exposed by a given
    Linux driver are handled gracefully: reads return a sensible default
    and writes are silently ignored.
    """

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

    @property
    def offset(self):
        """AD469x channel offset.

        Returns 0 for devices whose Linux driver does not expose offset
        (ad4691.c family: ad4691/92/93/94).
        """
        try:
            return self._get_iio_attr_str(self.name, "offset", False)
        except Exception:
            return "0"

    @offset.setter
    def offset(self, value):
        try:
            self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))
        except Exception:
            print(f"{self.name}: offset attribute not supported by this device")

    @property
    def oversampling_ratio(self):
        """
        AD469x channel oversampling ratio.

        Available in CNV burst mode (ad4691.c) or PWM-triggered mode
        (ad4695.c). Returns None when the current operating mode does
        not support oversampling.
        """
        try:
            return self._get_iio_attr(self.name, "oversampling_ratio", False)
        except Exception:
            return None

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        self._set_iio_attr(self.name, "oversampling_ratio", False, str(int(value)))

    @property
    def sampling_frequency(self):
        """AD469x channel sampling frequency in Hz."""
        try:
            return self._get_iio_attr(self.name, "sampling_frequency", False)
        except Exception:
            return None

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr(self.name, "sampling_frequency", False, str(int(value)))

    @property
    def calibscale(self):
        """
        AD469x channel calibration scale (ad4695.c family only).

        Returns None for devices whose Linux driver does not expose this
        attribute (ad4691.c family: ad4691/92/93/94).
        """
        try:
            return float(self._get_iio_attr_str(self.name, "calibscale", False))
        except Exception:
            return None

    @calibscale.setter
    def calibscale(self, value):
        self._set_iio_attr(self.name, "calibscale", False, str(Decimal(value).real))

    @property
    def calibbias(self):
        """
        AD469x channel calibration bias (ad4695.c family only).

        Returns None for devices whose Linux driver does not expose this
        attribute (ad4691.c family: ad4691/92/93/94).
        """
        try:
            return self._get_iio_attr(self.name, "calibbias", False)
        except Exception:
            return None

    @calibbias.setter
    def calibbias(self, value):
        self._set_iio_attr(self.name, "calibbias", False, str(int(value)))


class ad469x(rx_chan_comp):
    """
    AD469x ADC.

    Supports the ad4695.c Linux driver family (ad4695/96/97/98) and the
    ad4691.c Linux driver family (ad4691/92/93/94). Both families share
    the same IIO interface for raw reads and buffered captures; optional
    per-channel attributes (offset, oversampling_ratio, sampling_frequency,
    calibscale, calibbias) are exposed where the underlying driver supports
    them and return safe defaults otherwise.
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
