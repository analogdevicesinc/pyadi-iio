# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.rx_tx import tx_def


class ad9739a(tx_def):
    """ AD9739A 14-Bit, 2.5 GSPS, RF Digital-to-Analog Converter """

    compatible_parts = ["ad9739a"]
    _tx_data_device_name = "axi-ad9739a-hpc"
    _control_device_name = "axi-ad9739a-hpc"
    _complex_data = False
    _tx_channel_names = ["voltage0"]

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", True, value, self._txdac)
