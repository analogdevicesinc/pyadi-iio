# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from numpy import min


class _dec_int_fpga_filter:
    """Decimator and interpolator fpga filter controls"""

    def _get_rates(self, dev, output):
        """Get the decimation and interpolation rates"""
        sfa = self._get_iio_attr_str(
            "voltage0", "sampling_frequency_available", output, dev
        )
        rates = sfa.strip().replace("[", "").replace("]", "").split(" ")
        return [int(rate) for rate in rates]

    @property
    def rx_dec8_filter_en(self) -> bool:
        """rx_dec8_filter_en: Enable decimate by 8 filter in FPGA"""
        rates = self._get_rates(self._rxadc, False)
        sf = self._get_iio_attr("voltage0", "sampling_frequency", False, self._rxadc)
        return sf == min(rates)

    @rx_dec8_filter_en.setter
    def rx_dec8_filter_en(self, value: bool):
        """rx_dec8_filter_en: Enable decimate by 8 filter in FPGA"""
        rates = self._get_rates(self._rxadc, False)
        sr = rates[1] if value else rates[0]
        self._set_iio_attr("voltage0", "sampling_frequency", False, sr, self._rxadc)

    @property
    def tx_int8_filter_en(self) -> bool:
        """tx_int8_filter_en: Enable interpolate by 8 filter in FPGA"""
        rates = self._get_rates(self._txdac, True)
        sf = self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)
        return sf == min(rates)

    @tx_int8_filter_en.setter
    def tx_int8_filter_en(self, value: bool):
        """tx_int8_filter_en: Enable interpolate by 8 filter in FPGA"""
        rates = self._get_rates(self._txdac, True)
        sr = rates[1] if value else rates[0]
        self._set_iio_attr("voltage0", "sampling_frequency", True, sr, self._txdac)
