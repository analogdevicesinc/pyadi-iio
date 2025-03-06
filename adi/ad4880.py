# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad4880(rx, context_manager):

    """ AD4880 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name="ad4880"):

        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4880", "ad4880_chb"]
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

    class _channel(attribute):
        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            """"""
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def lvds_cnv(self):
            """"""
            return self._get_iio_attr(self.name, "lvds_cnv", False)

        @lvds_cnv.setter
        def lvds_cnv(self, calibscale):
            """"""
            self._set_iio_attr(self.name, "lvds_cnv", False, calibscale, self._ctrl)

        @property
        def lvds_sync(self):
            """"""
            return self._get_iio_attr(self.name, "lvds_sync", False)

        @lvds_sync.setter
        def lvds_sync(self, lvds_sync):
            """"""
            self._set_iio_attr(self.name, "lvds_sync", False, lvds_sync, self._ctrl)

    @property
    def sampling_frequency(self):
        """sampling_frequency: Sampling frequency value"""
        return self._get_iio_dev_attr("sampling_frequency", False)

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

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
