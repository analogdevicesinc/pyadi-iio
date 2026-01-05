# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4080(rx, context_manager):

    """ AD4080 ADC """

    _complex_data = False
    _device_name = ""
    channel = []  # type: ignore

    def __init__(self, uri="", device_name="ad4080"):
        context_manager.__init__(self, uri, self._device_name)

        compatible_part = "ad4080"
        self._ctrl = None

        if not device_name:
            device_name = compatible_part
        else:
            if device_name != compatible_part:
                raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("AD4080 device not found")

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
        """AD4080 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            """Get Scale value"""
            return self._get_iio_attr("voltage0", "scale", False)

    @property
    def sampling_frequency(self):
        """Get Sampling frequency value"""
        return self._get_iio_dev_attr("sampling_frequency", False)

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

    @property
    def filter_type_available(self):
        """Get the filter type available values"""
        return self._get_iio_dev_attr_str("filter_type_available", False)

    @property
    def filter_type(self):
        """Get the filter type value"""
        return self._get_iio_dev_attr_str("filter_type", False)

    @filter_type.setter
    def filter_type(self, value):
        """Set the filter type value"""
        self._set_iio_dev_attr_str("filter_type", value)

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
