# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7768(rx, context_manager):

    """ AD7768 8-channel, Simultaneous Sampling Sigma-Delta ADC """

    _device_name = " "
    _rx_data_type = np.int32

    def __init__(
        self, uri="ip:analog.local",
    ):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ad7768")
        self._rxadc = self._ctx.find_device("ad7768")
        self._device_name = "ad7768"

        if not self._rxadc:
            self._ctrl = self._ctx.find_device("cf_axi_adc")
            self._rxadc = self._ctx.find_device("cf_axi_adc")
            self._device_name = "cf_axi_adc"

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._rxadc:
            raise Exception("Error in selecting matching device")

        self._rx_channel_names = []
        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)

        rx.__init__(self)

    @property
    def sampling_frequency_available(self):
        """Get available sampling frequencies."""
        return self._get_iio_dev_attr("sampling_frequency_available")

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        if rate in self.sampling_frequency_available:
            self._set_iio_dev_attr("sampling_frequency", rate)
        else:
            raise ValueError(
                "Error: Sampling frequency not supported \nUse one of: "
                + str(self.sampling_frequency_available)
            )

    @property
    def power_mode_avail(self):
        """Get available power modes."""
        return self._get_iio_dev_attr_str("power_mode_available")

    @property
    def power_mode(self):
        """Get power mode."""
        return self._get_iio_dev_attr_str("power_mode")

    @power_mode.setter
    def power_mode(self, mode):
        """Set power mode."""
        if mode in self.power_mode_avail:
            self._set_iio_dev_attr_str("power_mode", mode)
        else:
            raise ValueError(
                "Error: Power mode not supported \nUse one of: "
                + str(self.power_mode_avail)
            )

    @property
    def filter_type_avail(self):
        """Get available filter types."""
        return self._get_iio_dev_attr_str("filter_type_available")

    @property
    def filter_type(self):
        """Get filter type."""
        return self._get_iio_dev_attr_str("filter_type")

    @filter_type.setter
    def filter_type(self, ftype):
        """Set filter type."""
        if ftype in self.filter_type_avail:
            self._set_iio_dev_attr_str("filter_type", ftype)
        else:
            raise ValueError(
                "Error: Filter type not supported \nUse one of: "
                + str(self.filter_type_avail)
            )


class ad7768_4(ad7768):

    """ AD7768 4-channel, Simultaneous Sampling Sigma-Delta ADC """

    @property
    def sync_start_enable_available(self):
        """Get available sync start enable types."""
        return self._get_iio_dev_attr_str("sync_start_enable_available")

    @property
    def sync_start_enable(self):
        """Get sync start enable."""
        return self._get_iio_dev_attr_str("sync_start_enable")

    @sync_start_enable.setter
    def sync_start_enable(self, ftype):
        """Set sync start enable."""
        if ftype in self.sync_start_enable_available:
            self._set_iio_dev_attr_str("sync_start_enable", ftype)
        else:
            raise ValueError(
                "Error: Sync start enable not supported \nUse one of: "
                + str(self.sync_start_enable_available)
            )
