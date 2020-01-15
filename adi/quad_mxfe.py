# Copyright (C) 2019 Analog Devices, Inc.
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

from adi.context_manager import context_manager
from adi.rx_tx import rx_tx

# Class descriptors
class channel_multi:
    def __init__(self, attr, dev, channel_names, output):
        self._dev = dev
        self._attr = attr
        self._channel_names = channel_names
        self._output = output

    def __get__(self, instance, owner):
        return instance._get_iio_attr_vec(
            self._channel_names, self._attr, self._output, self._dev
        )

    def __set__(self, instance, values):
        instance._set_iio_attr_int_vec(
            self._channel_names, self._attr, self._output, values, self._dev
        )


class channel_single:
    def __init__(self, attr, dev, channel_names, output):
        self._dev = dev
        self._attr = attr
        self._channel_names = channel_names
        self._output = output

    def __get__(self, instance, owner):
        return instance._get_iio_attr_str(
            self._channel_names, self._attr, self._output, self._dev
        )

    def __set__(self, instance, value):
        instance._set_iio_attr(
            self._channel_names, self._attr, self._output, value, self._dev
        )


class QuadMxFE(rx_tx, context_manager):
    """ Quad AD9081 Mixed-Signal Front End (MxFE) Evaluation Board """

    _complex_data = True
    _rx_channel_names = []
    _tx_channel_names = []
    _rx_dds_channel_names = []
    _tx_main_channel_names = []
    _tx_chan_channel_names = []
    _dds_channel_names = []
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Default device for attribute writes
        self._ctrl = self._ctx.find_device("axi-ad9081-rx-3")
        # Devices with buffers
        self._rxadc = self._ctx.find_device("axi-ad9081-rx-3")
        self._txdac = self._ctx.find_device("axi-ad9081-tx-3")
        # Attribute only devices
        self._attenuator = self._ctx.find_device("hmc425a")
        self._rxadc0 = self._ctx.find_device("axi-ad9081-rx-0")
        self._rxadc1 = self._ctx.find_device("axi-ad9081-rx-1")
        self._rxadc2 = self._ctx.find_device("axi-ad9081-rx-2")
        self._rxadc3 = self._ctx.find_device("axi-ad9081-rx-3")
        self._clock_chip = self._ctx.find_device("hmc7043")
        self._pll0 = self._ctx.find_device("adf4371-0")
        self._pll1 = self._ctx.find_device("adf4371-1")
        self._pll2 = self._ctx.find_device("adf4371-2")
        self._pll3 = self._ctx.find_device("adf4371-3")
        adcs = [self._rxadc0, self._rxadc1, self._rxadc2, self._rxadc3]

        # Dynamically get channels
        dds_chans = []
        for ch in self._rxadc.channels:
            if ch._id.find("voltage_q") != -1:
                continue
            if ch.scan_element:
                self._rx_channel_names.append(ch._id)
            else:
                self._rx_dds_channel_names.append(ch._id)
                dds_chans.append(ch)
        for ch in self._txdac.channels:
            if ch._id.find("voltage_q") != -1:
                continue
            if ch.scan_element:
                self._tx_channel_names.append(ch._id)
            else:
                self._dds_channel_names.append(ch._id)

        # Sort converter channels
        def sortconv(chans_names):
            tmpI = filter(lambda k: "_i" in k, chans_names)
            tmpQ = filter(lambda k: "_q" in k, chans_names)

            def ignoreadc(w):
                return int(w[len("voltage") : w.find("_")])

            tmpI = sorted(tmpI, key=ignoreadc)
            tmpQ = sorted(tmpQ, key=ignoreadc)
            chans_names = []
            for i in range(len(tmpI)):
                chans_names.append(tmpI[i])
                chans_names.append(tmpQ[i])
            return chans_names

        self._rx_channel_names = sortconv(self._rx_channel_names)
        self._tx_channel_names = sortconv(self._tx_channel_names)

        # Sort dds channels
        def ignoredds(w):
            return int(w[len("altvoltage") :])

        self._dds_channel_names = sorted(self._dds_channel_names, key=ignoredds)

        rx_tx.__init__(self)
        self.rx_buffer_size = 2 ** 16

        # Driver structure
        # RX path (inputs)
        # - 32 buffered channels
        # -- 32 with test mode control
        # -- 8 channels with DDS Control
        # RX path (outputs)
        # - 8 channels with DDS Control (more complex)

        # axi-ad9081-rx0
        # - 8 input channels
        # - 8 output channels

        # Dynamically add methods for each RX channel
        for i, chan in enumerate(adcs):
            # Channel
            name = "rx_channel_nco_frequencies_chip_" + chr(i + 97)
            attr = "channel_nco_frequency"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, False),
            )
            name = "rx_channel_nco_phases_chip_" + chr(i + 97)
            attr = "channel_nco_phase"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, False),
            )

            # Main
            name = "rx_main_nco_frequencies_chip_" + chr(i + 97)
            attr = "main_nco_frequency"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, False),
            )
            name = "rx_main_nco_phases_chip_" + chr(i + 97)
            attr = "main_nco_phase"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, False),
            )

            # Singletons
            name = "rx_test_mode_chip_" + chr(i + 97)
            attr = "test_mode"
            setattr(
                type(self),
                name,
                channel_single(attr, adcs[i], self._rx_dds_channel_names[0], False),
            )

        # Dynamically add methods for each TX channel
        for i, chan in enumerate(adcs):
            # Channel
            name = "tx_channel_nco_frequencies_chip_" + chr(i + 97)
            attr = "channel_nco_frequency"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, True),
            )
            name = "tx_channel_nco_phases_chip_" + chr(i + 97)
            attr = "channel_nco_phase"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, True),
            )
            name = "tx_channel_nco_gain_scale_chip_" + chr(i + 97)
            attr = "channel_nco_gain_scale"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, True),
            )

            # Main
            name = "tx_main_nco_frequencies_chip_" + chr(i + 97)
            attr = "main_nco_frequency"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, True),
            )
            name = "tx_main_nco_phases_chip_" + chr(i + 97)
            attr = "main_nco_phase"
            setattr(
                type(self),
                name,
                channel_multi(attr, adcs[i], self._rx_dds_channel_names, True),
            )

    @property
    def rx_sampling_frequency(self):
        """rx_sampling_frequency: Sample rate after decimation"""
        return self._get_iio_attr("voltage0_i", "sampling_frequency", False)

    @property
    def tx_sampling_frequency(self):
        """tx_sampling_frequency: Sample rate before interpolation"""
        return self._get_iio_attr("voltage0_i", "sampling_frequency", True)

    @property
    def external_hardwaregain(self):
        """external_hardwaregain: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._attenuator)

    @external_hardwaregain.setter
    def external_hardwaregain(self, value):
        self._set_iio_attr(
            "voltage0", "hardwaregain", True, value, _ctrl=self._attenuator
        )
