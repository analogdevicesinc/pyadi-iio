# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class max31865(rx, context_manager, attribute):
    """MAX31865 RTD to Digital device"""

    _device_name = "max31865"
    _rx_data_type = np.int16
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("max31865")

        if self._ctrl is None:
            raise Exception("No device found")

        self.temp = self._channel_temp(self._ctrl, "temp")
        self.filter = self._channel_filt(self._ctrl, "filter")
        self._rx_channel_names = ["temp", "filter"]
        rx.__init__(self)

    @property
    def fault(self):
        """MAX31865 Over/Under Voltage Flag"""
        return self._get_iio_dev_attr("fault_ovuv")

    @property
    def samp_available(self):
        """MAX31865 Sampling frequency"""
        return self._get_iio_dev_attr("sampling_frequency_available")

    class _channel_temp(attribute):
        """MAX31865 temp channel"""

        def __init__(self, ctrl, channel_name):
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

    class _channel_filt(attribute):
        """MAX31865 filter channel"""

        def __init__(self, ctrl, channel_name):
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
