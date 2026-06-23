# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import Dict, List

from adi.context_manager import context_manager
from adi.rx_tx import rx
from adi.sync_start import sync_start


class ad9083(sync_start, rx, context_manager):
    """AD9083 High-Speed Multi-channel ADC"""

    _complex_data = False
    _rx_channel_names: List[str] = []

    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad9083-rx-hpc")
        if not self._rxadc:
            raise Exception("Cannot find device axi-ad9083-rx-hpc")

        self._rx_channel_names = []
        for ch in self._rxadc.channels:
            if ch.scan_element and not ch.output:
                self._rx_channel_names.append(ch._id)

        for name in self._rx_channel_names:
            if any(ext in name for ext in ["_i", "_q"]):
                self._complex_data = True

        rx.__init__(self)

    @property
    def rx_sample_rate(self):
        """rx_sampling_frequency: Sample rate after decimation"""
        return self._get_iio_attr(
            "voltage0_i", "sampling_frequency", False, self._rxadc
        )

    @property
    def nco0_frequency(self):
        """nco0_frequency: Get/Set NCO0 frequency"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._rxadc)

    @nco0_frequency.setter
    def nco0_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "frequency", True, int(value), self._rxadc
        )

    @property
    def nco1_frequency(self):
        """nco0_frequency: Get/Set NCO1 frequency"""
        return self._get_iio_attr("altvoltage1", "frequency", True, self._rxadc)

    @nco1_frequency.setter
    def nco1_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "frequency", True, int(value), self._rxadc
        )

    @property
    def nco2_frequency(self):
        """nco0_frequency: Get/Set NCO2 frequency"""
        return self._get_iio_attr("altvoltage2", "frequency", True, self._rxadc)

    @nco2_frequency.setter
    def nco2_frequency(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "frequency", True, int(value), self._rxadc
        )

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._rxadc)
        return self._get_iio_debug_attr_str("direct_reg_access", self._rxadc)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._rxadc)
