# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import Dict, List

from adi.adrv9002 import rx1, rx2, tx1, tx2
from adi.context_manager import context_manager
from adi.obs import obs, remap, tx_two
from adi.rx_tx import rx_tx
from adi.sync_start import sync_start, sync_start_b


def _map_to_dict(paths, ch):
    if ch.attrs["label"].value == "buffer_only":
        return paths
    side, fddc, cddc, adc = ch.attrs["label"].value.replace(":", "->").split("->")
    if side not in paths.keys():
        paths[side] = {}
    if adc not in paths[side].keys():
        paths[side][adc] = {}
    if cddc not in paths[side][adc].keys():
        paths[side][adc][cddc] = {}
    if fddc not in paths[side][adc][cddc].keys():
        paths[side][adc][cddc][fddc] = {"channels": [ch._id]}
    else:
        paths[side][adc][cddc][fddc]["channels"].append(ch._id)
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


class ad9084(rx_tx, context_manager, sync_start, sync_start_b):
    """AD9084 Mixed-Signal Front End (MxFE)"""

    _complex_data = True
    _rx_channel_names: List[str] = []
    _rx2_channel_names: List[str] = []
    _tx_channel_names: List[str] = []
    _tx2_channel_names: List[str] = []
    _tx_control_channel_names: List[str] = []
    _rx_coarse_ddc_channel_names: List[str] = []
    _tx_coarse_duc_channel_names: List[str] = []
    _rx_fine_ddc_channel_names: List[str] = []
    _tx_fine_duc_channel_names: List[str] = []
    _dds_channel_names: List[str] = []
    _dds2_channel_names: List[str] = []
    _device_name = ""

    _path_map: Dict[str, Dict[str, Dict[str, List[str]]]] = {}

    def __init__(
        self,
        uri="",
        rx1_device_name="axi-ad9084-rx-hpc",
        rx2_device_name="axi-ad9084b-rx-b",
        tx1_device_name="axi-ad9084-tx-hpc",
        tx2_device_name="axi-ad9084-tx-b",
    ):
        """Create a new instance of the AD9084 MxFE

        rx1_device_name is used as the name for the control device and RX1/TX1 data device

        Args:
            uri: URI of device
            rx1_device_name: Name of RX1 device driver. Default is 'axi-ad9084-rx-hpc'
            rx2_device_name: Name of RX2 device driver. Default is 'axi-ad9084b-rx-b'
            tx1_device_name: Name of TX1 device driver. Default is 'axi-ad9084-tx-hpc'
            tx2_device_name: Name of TX2 device driver. Default is 'axi-ad9084-tx-b'
        """
        # Reset default channel lists
        self._rx_channel_names = []
        self._tx_channel_names = []
        self._tx_control_channel_names = []
        self._rx_coarse_ddc_channel_names = []
        self._tx_coarse_duc_channel_names = []
        self._rx_fine_ddc_channel_names = []
        self._tx_fine_duc_channel_names = []
        self._dds_channel_names = []

        context_manager.__init__(self, uri, self._device_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device(rx1_device_name)
        # Devices with buffers
        self._rxadc = self._ctx.find_device(rx1_device_name)
        self._txdac = self._ctx.find_device(tx1_device_name)
        self._rxadc2 = self._ctx.find_device(rx2_device_name)
        self._txdac2 = self._ctx.find_device(tx2_device_name)
        if self._rxadc is None or self._txdac is None:
            raise Exception("No AD9084 device found")
        single_link = self._rxadc2 is None or self._txdac2 is None

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
        if not single_link:
            for ch in self._rxadc2.channels:
                if ch.scan_element and not ch.output:
                    self._rx2_channel_names.append(ch._id)
            for ch in self._txdac2.channels:
                if ch.scan_element:
                    self._tx2_channel_names.append(ch._id)
                else:
                    self._dds2_channel_names.append(ch._id)

        # Sort channel names
        self._rx_channel_names = _sortconv(self._rx_channel_names)
        self._tx_channel_names = _sortconv(self._tx_channel_names)
        self._dds_channel_names = _sortconv(self._dds_channel_names, dds=True)
        if not single_link:
            self._rx2_channel_names = _sortconv(self._rx2_channel_names)
            self._tx2_channel_names = _sortconv(self._tx2_channel_names)
            self._dds2_channel_names = _sortconv(self._dds2_channel_names, dds=True)

        # Map unique attributes to channel properties
        self._rx_fine_ddc_channel_names = []
        self._rx_coarse_ddc_channel_names = []
        self._tx_fine_duc_channel_names = []
        self._tx_coarse_duc_channel_names = []

        for side in paths:
            for converter in paths[side]:
                for cdc in paths[side][converter]:
                    channels = []
                    for fdc in paths[side][converter][cdc]:
                        channels += paths[side][converter][cdc][fdc]["channels"]
                    channels = [name for name in channels if "_i" in name]
                    if "ADC" in converter:
                        self._rx_coarse_ddc_channel_names.append(channels[0])
                        self._rx_fine_ddc_channel_names += channels
                    else:
                        self._tx_coarse_duc_channel_names.append(channels[0])
                        self._tx_fine_duc_channel_names += channels

        # Setup second DMA path
        if not single_link:
            self._rx2 = obs(self._ctx, self._rxadc2, self._rx2_channel_names)
            setattr(ad9084, "rx1", rx1)
            setattr(ad9084, "rx2", rx2)
            remap(self._rx2, "rx_", "rx2_", type(self))

            self._tx2 = tx_two(self._ctx, self._txdac2, self._tx2_channel_names)
            setattr(ad9084, "tx1", tx1)
            setattr(ad9084, "tx2", tx2)
            remap(self._tx2, "tx_", "tx2_", type(self))
            remap(self._tx2, "dds_", "dds2_", type(self))

        rx_tx.__init__(self)
        sync_start.__init__(self)
        if not single_link:
            sync_start_b.__init__(self)

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
    def rx_main_tb1_6db_digital_gain_en(self):
        """main_tb1_6db_digital_gain_en: Receive path coarse DDC NCO phases"""
        return self._get_iio_attr_vec(
            self._rx_coarse_ddc_channel_names, "main_tb1_6db_digital_gain_en", False
        )

    @rx_main_tb1_6db_digital_gain_en.setter
    def rx_main_tb1_6db_digital_gain_en(self, value):
        self._set_iio_attr_int_vec(
            self._rx_coarse_ddc_channel_names,
            "main_tb1_6db_digital_gain_en",
            False,
            value,
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
    def tx_b_ddr_offload(self):
        """tx_b_ddr_offload: Enable DDR offload

        When true the DMA will pass buffers into the BRAM FIFO for data repeating.
        This is necessary when operating at high DAC sample rates. This can reduce
        the maximum buffer size but data passed to DACs in cyclic mode will not
        underflow due to memory bottlenecks.
        """
        return self._get_iio_debug_attr("pl_ddr_fifo_enable", self._txdac2)

    @tx_b_ddr_offload.setter
    def tx_b_ddr_offload(self, value):
        self._set_iio_debug_attr_str("pl_ddr_fifo_enable", str(value * 1), self._txdac2)

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

    @property
    def jesd204_device_status(self):
        """jesd204_device_status: Device jesd204 link status information"""
        return self._get_iio_debug_attr_str("status", self._rxadc)

    @property
    def jesd204_device_status_check(self):
        """jesd204_device_status_check: Device jesd204 link status check

        Returns 'True' in case error conditions are detected, 'False' otherwise
        """
        stat = self._get_iio_debug_attr_str("status", self._rxadc)

        for s in stat.splitlines(0):
            if "JRX" in s:
                if "204C" in s:
                    if "Link is good" not in s:
                        return True
                elif "204B" in s:
                    if "0x0 lanes in DATA" in s:
                        return True
            elif "JTX" in s:
                if any(
                    substr in s
                    for substr in [" asserted", "unlocked", "lost", "invalid"]
                ):
                    return True
        return False

    @property
    def chip_version(self):
        """chip_version: Chip version information"""
        return self._get_iio_debug_attr_str("chip_version", self._rxadc)

    @property
    def api_version(self):
        """api_version: API version"""
        return self._get_iio_debug_attr_str("api_version", self._rxadc)
