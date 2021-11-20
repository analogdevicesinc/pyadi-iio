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

from adi.ad9081 import ad9081
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.one_bit_adc_dac import one_bit_adc_dac
from adi.rx_tx import rx_tx


def _map_to_dict(paths, ch, dev_name):
    if "label" in ch.attrs and "buffer_only" in ch.attrs["label"].value:
        return paths, False
    fddc, cddc, adc = ch.attrs["label"].value.split("->")
    if dev_name not in paths.keys():
        paths[dev_name] = {}
    if adc not in paths[dev_name].keys():
        paths[dev_name][adc] = {}
    if cddc not in paths[dev_name][adc].keys():
        paths[dev_name][adc][cddc] = {}
    if fddc not in paths[dev_name][adc][cddc].keys():
        paths[dev_name][adc][cddc][fddc] = {"channels": [ch._id]}
    else:
        paths[dev_name][adc][cddc][fddc]["channels"].append(ch._id)
    return paths, True


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


def _find_dev_with_buffers(ctx, output=False, contains=""):
    for dev in ctx.devices:
        for chan in dev.channels:
            if (
                chan.output == output
                and chan.scan_element
                and dev.name
                and contains in dev.name
            ):
                return dev


class ad9081_mc(ad9081):
    """AD9081 Mixed-Signal Front End (MxFE) Multi-Chip Interface

        This class is a generic interface for boards that utilize multiple AD9081
        devices.

    parameters:
        uri: type=string
            Optional parameter for the URI of IIO context with AD9081(s).
        phy_dev_name: type=string
            Optional parameter name of main control driver for multi-AD9081 board.
            If no argument is given the driver with the most channel attributes is
            assumed to be the main PHY driver

    """

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

    def __init__(self, uri="", phy_dev_name=""):

        self._rx_channel_names: List[str] = []
        context_manager.__init__(self, uri, self._device_name)

        if not phy_dev_name:
            # Get ad9081 dev name with most channel attributes
            channel_attr_count = {
                dev.name: sum(len(chan.attrs) for chan in dev.channels)
                for dev in self._ctx.devices
                if dev.name and "ad9081" in dev.name
            }
            phy_dev_name = max(channel_attr_count, key=channel_attr_count.get)

        self._ctrl = self._ctx.find_device(phy_dev_name)
        if not self._ctrl:
            raise Exception("phy_dev_name not found with name: {}".format(phy_dev_name))

        # Find device with buffers
        self._txdac = _find_dev_with_buffers(self._ctx, True, "axi-ad9081")
        self._rxadc = _find_dev_with_buffers(self._ctx, False, "axi-ad9081")

        # Get DDC and DUC mappings
        # Labels span all devices so they must all be processed
        paths = {}
        self._default_ctrl_names = []
        for dev in self._ctx.devices:
            if dev.name and "ad9081" not in dev.name:
                continue
            for ch in dev.channels:
                not_buffer = False
                if "label" in ch.attrs:
                    paths, not_buffer = _map_to_dict(paths, ch, dev.name)
                if not_buffer and dev.name not in self._default_ctrl_names:
                    self._default_ctrl_names.append(dev.name)

        self._default_ctrl_names = sorted(self._default_ctrl_names)
        self._ctrls = [self._ctx.find_device(dn) for dn in self._default_ctrl_names]
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
        self._map_unique(paths)

        # Bring up DMA and DDS interfaces
        rx_tx.__init__(self)
        self.rx_buffer_size = 2 ** 16

    def _map_unique(self, paths):
        self._rx_fine_ddc_channel_names = {}
        self._rx_coarse_ddc_channel_names = {}
        self._tx_fine_duc_channel_names = {}
        self._tx_coarse_duc_channel_names = {}
        for chip in paths:
            for converter in paths[chip]:
                for cdc in paths[chip][converter]:
                    channels = []
                    for fdc in paths[chip][converter][cdc]:
                        channels += paths[chip][converter][cdc][fdc]["channels"]
                    channels = [name for name in channels if "_i" in name]

                    if "ADC" in converter:
                        if chip not in self._rx_coarse_ddc_channel_names.keys():
                            self._rx_coarse_ddc_channel_names[chip] = []
                        if chip not in self._rx_fine_ddc_channel_names.keys():
                            self._rx_fine_ddc_channel_names[chip] = []

                        self._rx_coarse_ddc_channel_names[chip].append(channels[0])
                        self._rx_fine_ddc_channel_names[chip] += channels
                    else:
                        if chip not in self._tx_coarse_duc_channel_names.keys():
                            self._tx_coarse_duc_channel_names[chip] = []
                        if chip not in self._tx_fine_duc_channel_names.keys():
                            self._tx_fine_duc_channel_names[chip] = []

                        self._tx_coarse_duc_channel_names[chip].append(channels[0])
                        self._tx_fine_duc_channel_names[chip] += channels

    def _map_inputs_to_dict(self, channel_names_dict, attr, output, values):
        if not isinstance(values, dict):
            # If passed an array it must be split across the devices
            # Check to make sure length is accurate
            d = self._get_iio_attr_vec(channel_names_dict, attr, output)
            t_len = sum(len(d[e]) for e in d)
            if len(values) != t_len:
                raise Exception("Input must be of length {}".format(t_len))
            h = {}
            c = 0
            for dev in self._default_ctrl_names:
                data_index = len(d[dev])
                h[dev] = values[c : c + data_index]
                c += data_index
            values = h
        return values

    def _map_inputs_to_dict_single(self, channel_names_dict, values):
        if not isinstance(values, dict):
            # If passed an array it must be split across the devices
            # Check to make sure length is accurate
            t_len = len(channel_names_dict)
            if len(values) != t_len:
                raise Exception("Input must be of length {}".format(t_len))
            h = {dev: values[i] for i, dev in enumerate(self._default_ctrl_names)}
            values = h
        return values

    # Vector function intercepts
    def _get_iio_attr_vec(self, channel_names_dict, attr, output):
        return {
            dev: ad9081._get_iio_attr_vec(
                self, channel_names_dict[dev], attr, output, self._ctx.find_device(dev),
            )
            for dev in channel_names_dict
        }

    def _set_iio_attr_int_vec(self, channel_names_dict, attr, output, values):
        values = self._map_inputs_to_dict(channel_names_dict, attr, output, values)
        for dev in channel_names_dict:
            ad9081._set_iio_attr_int_vec(
                self,
                channel_names_dict[dev],
                attr,
                output,
                values[dev],
                self._ctx.find_device(dev),
            )

    def _set_iio_attr_float_vec(self, channel_names_dict, attr, output, values):
        values = self._map_inputs_to_dict(channel_names_dict, attr, output, values)
        for dev in channel_names_dict:
            ad9081._set_iio_attr_float_vec(
                self,
                channel_names_dict[dev],
                attr,
                output,
                values[dev],
                self._ctx.find_device(dev),
            )

    # Singleton function intercepts
    def _get_iio_attr_str_single(self, channel_name, attr, output):
        channel_names_dict = self._rx_coarse_ddc_channel_names
        return {
            dev: attribute._get_iio_attr_str(
                self, channel_name, attr, output, self._ctx.find_device(dev)
            )
            for dev in channel_names_dict
        }

    def _get_iio_attr_single(self, channel_name, attr, output):
        channel_names_dict = self._rx_coarse_ddc_channel_names
        return {
            dev: attribute._get_iio_attr(
                self, channel_name, attr, output, self._ctx.find_device(dev)
            )
            for dev in channel_names_dict
        }

    def _set_iio_attr_single(self, channel_name, attr, output, values):
        channel_names_dict = self._rx_coarse_ddc_channel_names
        values = self._map_inputs_to_dict_single(channel_names_dict, values)
        for dev in channel_names_dict:
            self._set_iio_attr(
                channel_name, attr, output, values[dev], self._ctx.find_device(dev)
            )

    def _get_iio_dev_attr_single(self, attr):
        channel_names_dict = self._rx_coarse_ddc_channel_names
        return {
            dev: attribute._get_iio_dev_attr(self, attr, self._ctx.find_device(dev))
            for dev in channel_names_dict
        }

    def _set_iio_dev_attr_single(self, attr, values):
        channel_names_dict = self._rx_coarse_ddc_channel_names
        values = self._map_inputs_to_dict_single(channel_names_dict, values)
        for dev in channel_names_dict:
            self._set_iio_dev_attr(attr, values[dev], self._ctx.find_device(dev))


class QuadMxFE(ad9081_mc):
    """Quad AD9081 Mixed-Signal Front End (MxFE) Development System

    parameters:
        uri: type=string
            Optional parameter for the URI of IIO context with QuadMxFE.
    """

    def __init__(self, uri="", calibration_board_attached=False):
        ad9081_mc.__init__(self, uri=uri, phy_dev_name="axi-ad9081-rx-3")
        one_bit_adc_dac.__init__(self, uri)

        self._clock_chip = self._ctx.find_device("hmc7043")

        self._rx_dsa = self._ctx.find_device("hmc425a")
        if not self._rx_dsa:
            self._rx_dsa = self._ctx.find_device("hmc540s")

        if calibration_board_attached:
            self._ad5592r = self._ctx.find_device("ad5592r")
            self._cb_gpio = self._ctx.find_device("one-bit-adc-dac")

    @property
    def rx_dsa_gain(self):
        """rx_dsa_gain: Receiver digital step attenuator gain"""
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._rx_dsa)

    @rx_dsa_gain.setter
    def rx_dsa_gain(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value, self._rx_dsa)
