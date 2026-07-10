# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class max31865_channel_temp(attribute):
    """MAX31865 temp channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX31865 temperature channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """MAX31865 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """MAX31865 channel scale value"""
        return self._get_iio_attr(self.name, "scale", False)


class max31865_channel_filt(attribute):
    """MAX31865 filter channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX31865 filter channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def notch(self):
        """MAX31865 Notch center frequency"""
        return self._get_iio_attr(self.name, "notch_center_frequency", False)

    @notch.setter
    def notch(self, value):
        """MAX31865 Notch center frequency (50 or 60)"""
        return self._set_iio_attr(self.name, "notch_center_frequency", False, value)


class max31865(rx_chan_comp):
    """MAX31865 RTD to Digital device"""

    _device_name = "max31865"
    _rx_data_type = np.int16
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _complex_data = False
    _rx_channel_names = ["temp", "filter"]
    # The filter channel has no scale attribute, so keep it out of the
    # auto-populated channel list and attach it manually below.
    _ignore_channels = ["filter"]
    compatible_parts = ["max31865"]

    def __post_init__(self):
        """Attach the non-scan-element filter channel."""
        self.filter = max31865_channel_filt(self._ctrl, "filter")

    def _channel_def(self, ctrl, name):
        if name == "filter":
            return max31865_channel_filt(ctrl, name)
        return max31865_channel_temp(ctrl, name)

    @property
    def fault(self):
        """MAX31865 Over/Under Voltage Flag"""
        return self._get_iio_dev_attr("fault_ovuv")

    @property
    def samp_available(self):
        """MAX31865 Sampling frequency"""
        return self._get_iio_dev_attr("sampling_frequency_available")
