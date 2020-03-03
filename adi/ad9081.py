# Copyright (C) 2020 Analog Devices, Inc.
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

from typing import List

from adi.context_manager import context_manager
from adi.rx_tx import rx_tx


class ad9081(rx_tx, context_manager):
    """ AD9081 Mixed-Signal Front End (MxFE) """

    _complex_data = True
    _rx_channel_names: List[str] = []
    _tx_channel_names: List[str] = []
    _rx_coarse_ddc_channel_names: List[str] = []
    _tx_coarse_duc_channel_names: List[str] = []
    _rx_fine_ddc_channel_names: List[str] = []
    _tx_fine_duc_channel_names: List[str] = []
    _dds_channel_names: List[str] = []
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("axi-ad9081-rx")
        # Devices with buffers
        self._rxadc = self._ctx.find_device("axi-ad9081-rx")
        self._txdac = self._ctx.find_device("axi-ad9081-tx")

        # Dynamically ADC get channels
        for ch in self._rxadc.channels:
            if ch.scan_element:
                if not ch.output:
                    self._rx_channel_names.append(ch._id)

        # Coarse DDC and DUC channels is always fixed but map to names based on fine stages
        coarse_ddc_channels = 4
        self._rx_coarse_ddc_channel_names = []
        indx = 0
        stride = len(self._rx_channel_names) // 2 // coarse_ddc_channels
        for _ in range(coarse_ddc_channels):
            self._rx_coarse_ddc_channel_names.append("voltage{}_i".format(indx))
            indx += stride

        # Dynamically DAC get channels
        for ch in self._txdac.channels:
            if ch.scan_element:
                if ch.output:
                    self._tx_channel_names.append(ch._id)

        coarse_duc_channels = 4
        indx = 0
        stride = len(self._tx_channel_names) // 2 // coarse_duc_channels
        for _ in range(coarse_ddc_channels):
            self._tx_coarse_duc_channel_names.append("voltage{}_i".format(indx))
            indx += stride

        # Get DDS channels
        for ch in self._txdac.channels:
            if "altvoltage" in ch._id:
                self._dds_channel_names.append(ch._id)

        # Sort converter channels
        def sortconv(chans_names, noq=False):
            tmpI = filter(lambda k: "_i" in k, chans_names)
            tmpQ = filter(lambda k: "_q" in k, chans_names)

            def ignoreadc(w):
                return int(w[len("voltage") : w.find("_")])

            tmpI = sorted(tmpI, key=ignoreadc)
            tmpQ = sorted(tmpQ, key=ignoreadc)
            chans_names = []
            for i in range(len(tmpI)):
                chans_names.append(tmpI[i])
                if not noq:
                    chans_names.append(tmpQ[i])
            return chans_names

        self._rx_channel_names = sortconv(self._rx_channel_names)
        self._tx_channel_names = sortconv(self._tx_channel_names)

        self._tx_coarse_duc_channel_names = sortconv(
            self._tx_coarse_duc_channel_names, True
        )
        self._rx_coarse_ddc_channel_names = sortconv(
            self._rx_coarse_ddc_channel_names, True
        )

        # Sort dds channels
        def ignoredds(w):
            return int(w[len("altvoltage") :])

        self._dds_channel_names = sorted(self._dds_channel_names, key=ignoredds)

        rx_tx.__init__(self)
        self.rx_buffer_size = 2 ** 16

    @property
    def rx_channel_nco_frequencies(self):
        """rx_channel_nco_frequencies: Receive path fine DDC NCO frequencies
        """
        return self._get_iio_attr_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_frequency", False
        )

    @rx_channel_nco_frequencies.setter
    def rx_channel_nco_frequencies(self, value):
        self._set_iio_attr_vec(
            self._rx_fine_ddc_channel_names,
            "channel_nco_frequency",
            False,
            value,
            self._rxadc,
        )

    @property
    def rx_channel_nco_phases(self):
        """rx_channel_nco_phases: Receive path fine DDC NCO phases
        """
        return self._get_iio_attr_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_phase", False
        )

    @rx_channel_nco_phases.setter
    def rx_channel_nco_phases(self, value):
        self._set_iio_attr_vec(
            self._rx_fine_ddc_channel_names,
            "channel_nco_phase",
            False,
            value,
            self._rxadc,
        )

    @property
    def rx_main_nco_frequencies(self):
        """rx_main_nco_frequencies: Receive path coarse DDC NCO frequencies
        """
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_frequency", False
        )

    @rx_main_nco_frequencies.setter
    def rx_main_nco_frequencies(self, value):
        self._set_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_frequency", False, value,
        )

    @property
    def rx_main_nco_phases(self):
        """rx_main_nco_phases: Receive path coarse DDC NCO phases
        """
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_phase", False
        )

    @rx_main_nco_phases.setter
    def rx_main_nco_phases(self, value):
        self._set_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_phase", False, value,
        )

    @property
    def rx_test_mode(self):
        """rx_test_mode: NCO Test Mode """
        return self._get_iio_attr("voltage0_i", "test_mode", False)

    @rx_test_mode.setter
    def rx_test_mode(self, value):
        self._set_iio_attr_str(
            "voltage0_i", "test_mode", False, value,
        )

    @property
    def rx_sampling_frequency(self):
        """rx_sampling_frequency: Sample rate after decimation"""
        return self._get_iio_attr("voltage0_i", "sampling_frequency", False)

    @property
    def tx_sampling_frequency(self):
        """tx_sampling_frequency: Sample rate before interpolation"""
        return self._get_iio_attr("voltage0_i", "sampling_frequency", True)
