# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4858(rx, context_manager):

    """ AD4858 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for ad4858 class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4858"]

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

        self._rx_channel_names = []
        self.channel = []
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
    def sampling_frequency(self, value):
        """Set sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", value)

    @property
    def oversampling_ratio_avail(self):
        """Get list of all available oversampling rates."""
        return self._get_iio_dev_attr_str("oversampling_ratio_available")

    @property
    def oversampling_ratio(self):
        """Get oversampling ratio."""
        return self._get_iio_dev_attr_str("oversampling_ratio")

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        """Set oversampling ratio."""
        if value in self.oversampling_ratio_avail:
            self._set_iio_dev_attr_str("oversampling_ratio", value)
        else:
            raise ValueError(
                "Error: oversampling ratio not supported \nUse one of: "
                + str(self.oversampling_ratio_avail)
            )

    @property
    def packet_format_avail(self):
        """Get list of all available packet formats."""
        return self._get_iio_dev_attr_str("packet_format_available")

    @property
    def packet_format(self):
        """Get packet format."""
        return self._get_iio_dev_attr_str("packet_format")

    @packet_format.setter
    def packet_format(self, value):
        """Set packet format."""
        if value in self.packet_format_avail:
            self._set_iio_dev_attr_str("packet_format", value)
        else:
            raise ValueError(
                "Error: packet format not supported \nUse one of: "
                + str(self.packet_format_avail)
            )

    class _channel(attribute):

        """ ad4858 channel """

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
        def calibbias(self):
            """Get calibration bias/offset value."""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            """Set channel calibration bias/offset."""
            self._set_iio_attr(self.name, "calibbias", False, value)

        @property
        def calibphase(self):
            """Get calibration phase value."""
            return self._get_iio_attr(self.name, "calibphase", False)

        @calibphase.setter
        def calibphase(self, value):
            """Set channel calibration phase."""
            self._set_iio_attr(self.name, "calibphase", False, value)

        @property
        def hardwaregain(self):
            """Get calibration gain value."""
            return self._get_iio_attr(self.name, "hardwaregain", False)

        @hardwaregain.setter
        def hardwaregain(self, value):
            """Set channel calibration gain."""
            self._set_iio_attr(self.name, "hardwaregain", False, value)

        @property
        def softspan_avail(self):
            """Get list of all available softspans."""
            return self._get_iio_attr_str(self.name, "softspan_available", False)

        @property
        def softspan(self):
            """Get softspan value."""
            return self._get_iio_attr_str(self.name, "softspan", False)

        @softspan.setter
        def softspan(self, value):
            """Set softspan value."""
            if value in self.softspan_avail:
                self._set_iio_attr(self.name, "softspan", False, value)
            else:
                raise ValueError(
                    "Error: softspan not supported \nUse one of: "
                    + str(self.softspan_avail)
                )

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int32):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        if ret is None:
            raise Exception("Error in converting to actual voltage")

        return ret
