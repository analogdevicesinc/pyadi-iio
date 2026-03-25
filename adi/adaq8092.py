# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


class adaq8092(rx, context_manager):

    """ADAQ8092 14-Bit, 105MSPS, Dual-Channel uModule Data Acquisition Solution"""

    _device_name = "adaq8092"
    _rx_stack_interleaved = True
    _rx_data_type = np.int16

    def __init__(
        self, uri="",
    ):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("adaq8092")
        self._rxadc = self._ctx.find_device("adaq8092")
        self._device_name = "adaq8092"
        if not self._rxadc:
            self._ctrl = self._ctx.find_device("cf_axi_adc")
            self._rxadc = self._ctx.find_device("cf_axi_adc")
            self._device_name = "cf_axi_adc"

        self._rx_channel_names = []
        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)
        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get Sampling Frequency."""
        return self._get_iio_dev_attr("sampling_frequency")
