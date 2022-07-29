# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
