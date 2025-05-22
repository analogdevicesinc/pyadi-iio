# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4851(rx, context_manager):

    """ AD4851 ADC """

    _complex_data = False
    _device_name = ""
    channel = []  # type: ignore

    def __init__(self, uri="", device_name="ad4851"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad4851",
            "ad4852",
            "ad4853",
            "ad4854",
            "ad4855",
            "ad4856",
            "ad4857",
            "ad4858",
            "ad4858i",
        ]
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

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception(f"{device_name} device not found")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        self._rx_channel_names = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch.id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    class _channel(attribute):
        """AD4851 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale_available(self):
            """Get Scale available values"""
            return self._get_iio_attr(self.name, "scale_available", False)

        @property
        def scale(self):
            """Get Scale value"""
            return self._get_iio_attr(self.name, "scale", False)

        @scale.setter
        def scale(self, value):
            """Set scale value"""
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

        @property
        def calibbias(self):
            """Get calibration bias/offset value."""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            """Set channel calibration bias/offset."""
            self._set_iio_attr(self.name, "calibbias", False, value)

        @property
        def calibscale(self):
            """Get calibration scale value."""
            return self._get_iio_attr(self.name, "calibscale", False)

        @calibscale.setter
        def calibscale(self, value):
            """Set channel calibration phascalese."""
            self._set_iio_attr(self.name, "calibscale", False, value)

    @property
    def sampling_frequency(self):
        """Get Sampling frequency value"""
        return self._get_iio_dev_attr("sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", value)

    @property
    def oversampling_ratio_available(self):
        """Get the oversampling ratio available values"""
        return self._get_iio_dev_attr("oversampling_ratio_available", False)

    @property
    def oversampling_ratio(self):
        """Get the oversampling ratio value"""
        return self._get_iio_dev_attr("oversampling_ratio", False)

    @oversampling_ratio.setter
    def oversampling_ratio(self, value):
        """Set the oversampling ratio value"""
        self._set_iio_dev_attr("oversampling_ratio", value)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
