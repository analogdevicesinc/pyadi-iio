# Copyright (C) 2020-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7768_1(rx, context_manager):

    """ AD7768-1 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for ad7768_1 class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7768-1"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", rate)

    class _channel(attribute):

        """ ad7768-1 channel """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """Get channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """Get channel scale."""
            return self._get_iio_attr(self.name, "scale", False)

        @scale.setter
        def scale(self, value):
            """Set channel scale."""
            self._set_iio_attr(self.name, "scale", False, Decimal(value).real)

        @property
        def offset(self):
            """Get channel offset."""
            return self._get_iio_attr(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            """Set channel offset."""
            self._set_iio_attr(self.name, "offset", False, value)

        @property
        def filter_low_pass_3db_frequency_avail(self):
            """Get available low pass filter 3db frequencies."""
            return self._get_iio_attr_str(
                self.name, "filter_low_pass_3db_frequency_available", False
            )

        @property
        def filter_low_pass_3db_frequency(self):
            """Get low pass filter 3db frequency."""
            return self._get_iio_attr_str(
                self.name, "filter_low_pass_3db_frequency", False
            )

        @filter_low_pass_3db_frequency.setter
        def filter_low_pass_3db_frequency(self, freq):
            """Set low pass filter 3db frequency."""
            if freq in self.filter_low_pass_3db_frequency_avail:
                self._set_iio_attr(
                    self.name, "filter_low_pass_3db_frequency", False, freq
                )
            else:
                raise ValueError(
                    "Error: Low pass filter 3db frequency not supported \nUse one of: "
                    + str(self.filter_low_pass_3db_frequency_avail)
                )

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
