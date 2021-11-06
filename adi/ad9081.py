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

from typing import Dict, List

from adi.context_manager import context_manager
from adi.rx_tx import rx_tx


def _map_to_dict(paths, ch):
    fddc, cddc, adc = ch.attrs["label"].value.split("->")
    if adc not in paths.keys():
        paths[adc] = {}
    if cddc not in paths[adc].keys():
        paths[adc][cddc] = {}
    if fddc not in paths[adc][cddc].keys():
        paths[adc][cddc][fddc] = {"channels": [ch._id]}
    else:
        paths[adc][cddc][fddc]["channels"].append(ch._id)
    return paths


def _sortconv(chans_names, noq=False, dds=False):
    tmpI = filter(lambda k: "_i" in k, chans_names)
    tmpQ = filter(lambda k: "_q" in k, chans_names)

    def ignoreadc(w):
        return int(w[len("voltage") : w.find("_")])

    def ignorealt(w):
        return int(w[len("altvoltage") :])

    chans_names_out = []
    if dds:
        filt = ignorealt
        tmpI = chans_names
        noq = True
    else:
        filt = ignoreadc

    tmpI = sorted(tmpI, key=filt)
    tmpQ = sorted(tmpQ, key=filt)
    for i in range(len(tmpI)):
        chans_names_out.append(tmpI[i])
        if not noq:
            chans_names_out.append(tmpQ[i])

    return chans_names_out


class ad9081(rx_tx, context_manager):
    """AD9081 Mixed-Signal Front End (MxFE)"""

    _complex_data = True
    _rx_channel_names: List[str] = []
    _tx_channel_names: List[str] = []
    _tx_control_channel_names: List[str] = []
    _rx_coarse_ddc_channel_names: List[str] = []
    _tx_coarse_duc_channel_names: List[str] = []
    _rx_fine_ddc_channel_names: List[str] = []
    _tx_fine_duc_channel_names: List[str] = []
    _dds_channel_names: List[str] = []
    _device_name = ""

    _rx_attr_only_channel_names: List[str] = []
    _tx_attr_only_channel_names: List[str] = []

    _path_map: Dict[str, Dict[str, Dict[str, List[str]]]] = {}

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("axi-ad9081-rx-hpc")
        # Devices with buffers
        self._rxadc = self._ctx.find_device("axi-ad9081-rx-hpc")
        self._txdac = self._ctx.find_device("axi-ad9081-tx-hpc")

        # Get DDC and DUC mappings
        paths = {}

        for ch in self._rxadc.channels:
            if "label" in ch.attrs:
                paths = _map_to_dict(paths, ch)
        self._path_map = paths

        # Get data + DDS channels
        for ch in self._rxadc.channels:
            if ch.scan_element and not ch.output:
                self._rx_channel_names.append(ch._id)
        for ch in self._txdac.channels:
            if ch.scan_element:
                self._tx_channel_names.append(ch._id)
            else:
                self._dds_channel_names.append(ch._id)

        # Sort channel names
        self._rx_channel_names = _sortconv(self._rx_channel_names)
        self._tx_channel_names = _sortconv(self._tx_channel_names)
        self._dds_channel_names = _sortconv(self._dds_channel_names, dds=True)

        # Map unique attributes to channel properties
        self._rx_fine_ddc_channel_names = []
        self._rx_coarse_ddc_channel_names = []
        self._tx_fine_duc_channel_names = []
        self._tx_coarse_duc_channel_names = []
        for converter in paths:
            for cdc in paths[converter]:
                channels = []
                for fdc in paths[converter][cdc]:
                    channels += paths[converter][cdc][fdc]["channels"]
                channels = [name for name in channels if "_i" in name]
                if "ADC" in converter:
                    self._rx_coarse_ddc_channel_names.append(channels[0])
                    self._rx_fine_ddc_channel_names += channels
                else:
                    self._tx_coarse_duc_channel_names.append(channels[0])
                    self._tx_fine_duc_channel_names += channels

        rx_tx.__init__(self)
        self.rx_buffer_size = 2 ** 16

    def _get_iio_attr_str_single(self, channel_name, attr, output):
        # This is overridden by subclasses
        return self._get_iio_attr_str(channel_name, attr, output)

    def _set_iio_attr_str_single(self, channel_name, attr, output, value):
        # This is overridden by subclasses
        return self._set_iio_attr(channel_name, attr, output, value)

    def _get_iio_attr_single(self, channel_name, attr, output):
        # This is overridden by subclasses
        return self._get_iio_attr(channel_name, attr, output)

    def _set_iio_attr_single(self, channel_name, attr, output, value):
        # This is overridden by subclasses
        return self._set_iio_attr(channel_name, attr, output, value)

    def _get_iio_dev_attr_single(self, attr):
        # This is overridden by subclasses
        return self._get_iio_dev_attr(attr)

    def _set_iio_dev_attr_single(self, attr, value):
        # This is overridden by subclasses
        return self._set_iio_dev_attr(attr, value)

    def _get_iio_dev_attr_str_single(self, attr):
        # This is overridden by subclasses
        return self._get_iio_dev_attr_str(attr)

    def _set_iio_dev_attr_str_single(self, attr, value):
        # This is overridden by subclasses
        return self._set_iio_dev_attr_str(attr, value)

    @property
    def path_map(self):
        """path_map: Map of channelizers both coarse and fine to
        individual driver channel names
        """
        return self._path_map

    def write_pfilt_config(self, value):
        """Load a new PFILT configuration file
        Input is path to PFILT configuration file. Please see
        driver documentation about PFILT generation and limitations
        """
        with open(value, "r") as file:
            data = file.read()
        self._set_iio_dev_attr_str("filter_fir_config", data)

    # we cannot really get the profile. The driver will just throw EPERM
    pfilt_config = property(None, write_pfilt_config)

    @property
    def rx_channel_nco_frequencies(self):
        """rx_channel_nco_frequencies: Receive path fine DDC NCO frequencies"""
        return self._get_iio_attr_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_frequency", False
        )

    @rx_channel_nco_frequencies.setter
    def rx_channel_nco_frequencies(self, value):
        self._set_iio_attr_int_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_frequency", False, value
        )

    @property
    def rx_channel_nco_phases(self):
        """rx_channel_nco_phases: Receive path fine DDC NCO phases"""
        return self._get_iio_attr_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_phase", False
        )

    @rx_channel_nco_phases.setter
    def rx_channel_nco_phases(self, value):
        self._set_iio_attr_int_vec(
            self._rx_fine_ddc_channel_names, "channel_nco_phase", False, value,
        )

    @property
    def rx_main_nco_frequencies(self):
        """rx_main_nco_frequencies: Receive path coarse DDC NCO frequencies"""
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_frequency", False
        )

    @rx_main_nco_frequencies.setter
    def rx_main_nco_frequencies(self, value):
        self._set_iio_attr_int_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_frequency", False, value,
        )

    @property
    def rx_main_nco_phases(self):
        """rx_main_nco_phases: Receive path coarse DDC NCO phases"""
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_phase", False
        )

    @rx_main_nco_phases.setter
    def rx_main_nco_phases(self, value):
        self._set_iio_attr_int_vec(
            self._rx_coarse_ddc_channel_names, "main_nco_phase", False, value,
        )

    @property
    def rx_test_mode(self):
        """rx_test_mode: NCO Test Mode"""
        return self._get_iio_attr_str_single("voltage0_i", "test_mode", False)

    @rx_test_mode.setter
    def rx_test_mode(self, value):
        self._set_iio_attr_single(
            "voltage0_i", "test_mode", False, value,
        )

    @property
    def rx_nyquist_zone(self):
        """rx_nyquist_zone: ADC nyquist zone. Options are: odd, even"""
        return self._get_iio_attr_str_vec(
            self._rx_coarse_ddc_channel_names, "nyquist_zone", False
        )

    @rx_nyquist_zone.setter
    def rx_nyquist_zone(self, value):
        self._set_iio_attr_str_vec(
            self._rx_coarse_ddc_channel_names, "nyquist_zone", False, value,
        )

    @property
    def rx_main_6dB_digital_gains(self):
        """rx_main_6dB_digital_gains: Enable 6dB of gain per CDDC"""
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_6db_digital_gain_en", False
        )

    @rx_main_6dB_digital_gains.setter
    def rx_main_6dB_digital_gains(self, value):
        self._set_iio_attr_int_vec(
            self._rx_coarse_ddc_channel_names, "main_6db_digital_gain_en", False, value,
        )

    @property
    def rx_channel_6dB_digital_gains(self):
        """rx_channel_6dB_digital_gains: Enable 6dB of gain per FDDC"""
        return self._get_iio_attr_vec(
            self._rx_fine_ddc_channel_names, "channel_6db_digital_gain_en", False
        )

    @rx_channel_6dB_digital_gains.setter
    def rx_channel_6dB_digital_gains(self, value):
        self._set_iio_attr_int_vec(
            self._rx_fine_ddc_channel_names,
            "channel_6db_digital_gain_en",
            False,
            value,
        )

    @property
    def tx_channel_nco_frequencies(self):
        """tx_channel_nco_frequencies: Transmit path fine DUC NCO frequencies"""
        return self._get_iio_attr_vec(
            self._tx_fine_duc_channel_names, "channel_nco_frequency", True
        )

    @tx_channel_nco_frequencies.setter
    def tx_channel_nco_frequencies(self, value):
        self._set_iio_attr_int_vec(
            self._tx_fine_duc_channel_names, "channel_nco_frequency", True, value
        )

    @property
    def tx_channel_nco_phases(self):
        """tx_channel_nco_phases: Transmit path fine DUC NCO phases"""
        return self._get_iio_attr_vec(
            self._tx_fine_duc_channel_names, "channel_nco_phase", True
        )

    @tx_channel_nco_phases.setter
    def tx_channel_nco_phases(self, value):
        self._set_iio_attr_int_vec(
            self._tx_fine_duc_channel_names, "channel_nco_phase", True, value,
        )

    @property
    def tx_channel_nco_test_tone_en(self):
        """tx_channel_nco_test_tone_en: Transmit path fine DUC NCO test tone enable"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "channel_nco_test_tone_en", True
        )

    @tx_channel_nco_test_tone_en.setter
    def tx_channel_nco_test_tone_en(self, value):
        self._set_iio_attr_int_vec(
            self._tx_coarse_duc_channel_names, "channel_nco_test_tone_en", True, value,
        )

    @property
    def tx_channel_nco_test_tone_scales(self):
        """tx_channel_nco_test_tone_scales: Transmit path fine DUC NCO test tone scale"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "channel_nco_test_tone_scale", True
        )

    @tx_channel_nco_test_tone_scales.setter
    def tx_channel_nco_test_tone_scales(self, value):
        self._set_iio_attr_float_vec(
            self._tx_coarse_duc_channel_names,
            "channel_nco_test_tone_scale",
            True,
            value,
        )

    @property
    def tx_channel_nco_gain_scales(self):
        """tx_channel_nco_gain_scales Transmit path fine DUC NCO gain scale"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "channel_nco_gain_scale", True
        )

    @tx_channel_nco_gain_scales.setter
    def tx_channel_nco_gain_scales(self, value):
        self._set_iio_attr_float_vec(
            self._tx_coarse_duc_channel_names, "channel_nco_gain_scale", True, value,
        )

    @property
    def tx_main_nco_frequencies(self):
        """tx_main_nco_frequencies: Transmit path coarse DUC NCO frequencies"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "main_nco_frequency", True
        )

    @tx_main_nco_frequencies.setter
    def tx_main_nco_frequencies(self, value):
        self._set_iio_attr_int_vec(
            self._tx_coarse_duc_channel_names, "main_nco_frequency", True, value,
        )

    @property
    def tx_main_nco_phases(self):
        """tx_main_nco_phases: Transmit path coarse DUC NCO phases"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "main_nco_phase", True
        )

    @tx_main_nco_phases.setter
    def tx_main_nco_phases(self, value):
        self._set_iio_attr_int_vec(
            self._tx_coarse_duc_channel_names, "main_nco_phase", True, value,
        )

    @property
    def tx_main_nco_test_tone_en(self):
        """tx_main_nco_test_tone_en: Transmit path coarse DUC NCO test tone enable"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "main_nco_test_tone_en", True
        )

    @tx_main_nco_test_tone_en.setter
    def tx_main_nco_test_tone_en(self, value):
        self._set_iio_attr_int_vec(
            self._tx_coarse_duc_channel_names, "main_nco_test_tone_en", True, value,
        )

    @property
    def tx_main_nco_test_tone_scales(self):
        """tx_main_nco_test_tone_scales: Transmit path coarse DUC NCO test tone scale"""
        return self._get_iio_attr_vec(
            self._tx_coarse_duc_channel_names, "main_nco_test_tone_scale", True
        )

    @tx_main_nco_test_tone_scales.setter
    def tx_main_nco_test_tone_scales(self, value):
        self._set_iio_attr_float_vec(
            self._tx_coarse_duc_channel_names, "main_nco_test_tone_scale", True, value,
        )

    @property
    def tx_main_ffh_frequency(self):
        """tx_main_ffh_frequency: Transmitter fast frequency hop frequency. This will set
        The NCO frequency of the NCO selected from the bank defined by tx_main_ffh_index
        """
        return self._get_iio_attr_single("voltage0_i", "main_ffh_frequency", True)

    @tx_main_ffh_frequency.setter
    def tx_main_ffh_frequency(self, value):
        if self.tx_main_ffh_index == 0:
            raise Exception(
                "To set a FFH NCO bank frequency, tx_main_ffh_index must > 0"
            )
        self._set_iio_attr_single(
            "voltage0_i", "main_ffh_frequency", True, value,
        )

    @property
    def tx_main_ffh_index(self):
        """tx_main_ffh_index: Transmitter fast frequency hop NCO bank index"""
        return self._get_iio_attr_single("voltage0_i", "main_ffh_index", True)

    @tx_main_ffh_index.setter
    def tx_main_ffh_index(self, value):
        self._set_iio_attr_single(
            "voltage0_i", "main_ffh_index", True, value,
        )

    @property
    def tx_main_ffh_mode(self):
        """tx_main_ffh_mode: Set hop transition mode of NCOs Options are:
        phase_continuous, phase_incontinuous, and phase_coherent
        """
        return self._get_iio_attr_str_single("voltage0_i", "main_ffh_mode", True)

    @tx_main_ffh_mode.setter
    def tx_main_ffh_mode(self, value):
        self._set_iio_attr_single(
            "voltage0_i", "main_ffh_mode", True, value,
        )

    @property
    def tx_dac_en(self):
        """tx_dac_en: Enable DACs"""
        return self._get_iio_attr_vec(self._tx_coarse_duc_channel_names, "en", True)

    @tx_dac_en.setter
    def tx_dac_en(self, value):
        self._set_iio_attr_int_vec(
            self._tx_coarse_duc_channel_names, "en", True, value,
        )

    def set_tx_dac_full_scale_current(self, value):
        """tx_dac_full_scale_current: Set full scale current of DACs. This value
        is in microamps.
        """
        self._set_iio_debug_attr_str(
            "dac-full-scale-current-ua", str(value), self._rxadc
        )

    # we cannot read current as the driver will just throw EPERM
    tx_dac_full_scale_current = property(None, set_tx_dac_full_scale_current)

    @property
    def loopback_mode(self):
        """loopback_mode: Enable loopback mode RX->TX

        When enabled JESD RX FIFO is connected to JESD TX FIFO,
        making the entire datasource for the TX path the RX path. No
        data is passed into the TX path from off-chip when 1. For
        this mode to function correctly the JESD configuration
        between RX and TX must be identical and only use a single
        link.
        """
        return self._get_iio_dev_attr_single("loopback_mode")

    @loopback_mode.setter
    def loopback_mode(self, value):
        self._set_iio_dev_attr_single(
            "loopback_mode", value,
        )

    @property
    def tx_ddr_offload(self):
        """tx_ddr_offload: Enable DDR offload

        When true the DMA will pass buffers into the BRAM FIFO for data repeating.
        This is necessary when operating at high DAC sample rates. This can reduce
        the maximum buffer size but data passed to DACs in cyclic mode will not
        underflow due to memory bottlenecks.
        """
        return self._get_iio_debug_attr("pl_ddr_fifo_enable", self._txdac)

    @tx_ddr_offload.setter
    def tx_ddr_offload(self, value):
        self._set_iio_debug_attr_str("pl_ddr_fifo_enable", str(value * 1), self._txdac)

    @property
    def rx_sample_rate(self):
        """rx_sampling_frequency: Sample rate after decimation"""
        return self._get_iio_attr_single("voltage0_i", "sampling_frequency", False)

    @property
    def adc_frequency(self):
        """adc_frequency: ADC frequency in Hz"""
        return self._get_iio_attr_single("voltage0_i", "adc_frequency", False)

    @property
    def tx_sample_rate(self):
        """tx_sampling_frequency: Sample rate before interpolation"""
        return self._get_iio_attr_single("voltage0_i", "sampling_frequency", True)

    @property
    def dac_frequency(self):
        """dac_frequency: DAC frequency in Hz"""
        return self._get_iio_attr_single("voltage0_i", "dac_frequency", True)

    @property
    def jesd204_fsm_ctrl(self):
        """jesd204_fsm_ctrl: jesd204-fsm control"""
        return self._get_iio_dev_attr("jesd204_fsm_ctrl", self._rxadc)

    @jesd204_fsm_ctrl.setter
    def jesd204_fsm_ctrl(self, value):
        self._set_iio_dev_attr("jesd204_fsm_ctrl", value, self._rxadc)

    @property
    def jesd204_fsm_resume(self):
        """jesd204_fsm_resume: jesd204-fsm resume"""
        return self._get_iio_dev_attr("jesd204_fsm_resume", self._rxadc)

    @jesd204_fsm_resume.setter
    def jesd204_fsm_resume(self, value):
        self._set_iio_dev_attr_str("jesd204_fsm_resume", value, self._rxadc)

    @property
    def jesd204_fsm_state(self):
        """jesd204_fsm_state: jesd204-fsm state"""
        return self._get_iio_dev_attr_str("jesd204_fsm_state", self._rxadc)

    @property
    def jesd204_fsm_paused(self):
        """jesd204_fsm_paused: jesd204-fsm paused"""
        return self._get_iio_dev_attr("jesd204_fsm_paused", self._rxadc)

    @property
    def jesd204_fsm_error(self):
        """jesd204_fsm_error: jesd204-fsm error"""
        return self._get_iio_dev_attr("jesd204_fsm_error", self._rxadc)
