# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.device_base import tx_def
from adi.sync_start import sync_start


class ad9152(tx_def, sync_start):
    """ AD9152 High-Speed DAC """

    _complex_data = False
    _tx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""
    _control_device_name = None
    _tx_data_device_name = "axi-ad9152-hpc"
    compatible_parts = ["axi-ad9152-hpc"]

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", True, value, self._txdac)
