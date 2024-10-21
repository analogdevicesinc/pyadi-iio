# Copyright (C) 2022-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import tx
from adi.sync_start import sync_start


class ad9162(tx, context_manager, sync_start):
    """ AD9162 16-Bit, 12 GSPS, RF DAC """

    _complex_data = False
    # _complex_data = True
    _tx_channel_names = ["voltage0"]
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):

        context_manager.__init__(self, uri, self._device_name)

        self._jesd = jesd(uri, username=username, password=password)
        self._txdac = self._ctx.find_device("axi-ad9164-hpc")

        tx.__init__(self)

    @property
    def fir85_enable(self):
        return self._get_iio_attr("altvoltage0", "fir85_enable", True, self._txdac)

    @fir85_enable.setter
    def fir85_enable(self, value):
        self._set_iio_attr("voltage0", "fir85_enable", True, value, self._txdac)

    @property
    def sample_rate(self):
        """sample_rate: Sample frequency rate TX path in samples per second."""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)

    @property
    def scale(self):
        return self._get_iio_attr("voltage0", "scale", True, self._txdac)

    @property
    def frequency_nco(self):
        return self._get_iio_attr("altvoltage4", "frequency_nco", True, self._txdac)

    @frequency_nco.setter
    def frequency_nco(self, value):
        self._set_iio_attr("altvoltage4", "frequency_nco", True, value, self._txdac)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()

    def register_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._txdac)
        return self._get_iio_debug_attr_str("direct_reg_access", self._txdac)
    def register_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._txdac)
