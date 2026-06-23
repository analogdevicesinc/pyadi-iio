# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.device_base import rx_def


class adaq8092(rx_def):

    """ADAQ8092 14-Bit, 105MSPS, Dual-Channel uModule Data Acquisition Solution"""

    compatible_parts = ["adaq8092", "cf_axi_adc"]
    _rx_stack_interleaved = True
    _rx_data_type = np.int16
    _complex_data = False
    _control_device_name = "adaq8092"
    _rx_data_device_name = "adaq8092"

    def __post_init__(self):
        """Handle special device name discovery for adaq8092."""
        # Try to find adaq8092 first, fall back to cf_axi_adc
        if not self._rxadc:
            # Try alternative name
            self._ctrl = self._ctx.find_device("cf_axi_adc")
            self._rxadc = self._ctx.find_device("cf_axi_adc")
            if self._rxadc:
                self._rx_data_device_name = "cf_axi_adc"
                self._control_device_name = "cf_axi_adc"

    @property
    def sampling_frequency(self):
        """Get Sampling Frequency."""
        return self._get_iio_dev_attr("sampling_frequency")
