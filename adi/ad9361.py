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


class ad9361(rx_tx, context_manager):
    """ AD9361 Transceiver """

    _complex_data = True
    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _tx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ad9361-phy")
        self._rxadc = self._ctx.find_device("cf-ad9361-lpc")
        self._txdac = self._ctx.find_device("cf-ad9361-dds-core-lpc")

        rx_tx.__init__(self)

    @property
    def filter(self):
        """Load FIR filter file. Provide path to filter file to attribute"""
        return self._get_iio_dev_attr("filter_fir_config")

    @filter.setter
    def filter(self, value):
        with open(value, "r") as file:
            data = file.read()
        self.sample_rate = 3000000
        self._set_iio_attr("out", "voltage_filter_fir_en", False, 0)
        self._set_iio_dev_attr_str("filter_fir_config", data)
        self._set_iio_attr("out", "voltage_filter_fir_en", False, 1)

    @property
    def loopback(self):
        """loopback: Set loopback mode. Options are:
        0 (Disable), 1 (Digital), 2 (RF)"""
        return self._get_iio_debug_attr("loopback")

    @loopback.setter
    def loopback(self, value):
        self._set_iio_debug_attr_str("loopback", value)

    @property
    def gain_control_mode(self):
        """gain_control_mode: Mode of receive path AGC. Options are:
        slow_attack, fast_attack, manual"""
        return self._get_iio_attr("voltage0", "gain_control_mode", False)

    @gain_control_mode.setter
    def gain_control_mode(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain(self):
        """rx_hardwaregain: Gain applied to RX path. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain.setter
    def rx_hardwaregain(self, value):
        if self.gain_control_mode == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def tx_hardwaregain(self):
        """tx_hardwaregain: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage0", "hardwaregain", True)

    @tx_hardwaregain.setter
    def tx_hardwaregain(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value)

    @property
    def rx_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False)

    @rx_rf_bandwidth.setter
    def rx_rf_bandwidth(self, value):
        self._set_iio_attr("voltage0", "rf_bandwidth", False, value)

    @property
    def tx_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True)

    @tx_rf_bandwidth.setter
    def tx_rf_bandwidth(self, value):
        self._set_iio_attr("voltage0", "rf_bandwidth", True, value)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", False, value)

    @property
    def rx_lo(self):
        """rx_lo: Carrier frequency of RX path"""
        return self._get_iio_attr("altvoltage0", "frequency", True)

    @rx_lo.setter
    def rx_lo(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value)

    @property
    def tx_lo(self):
        """tx_lo: Carrier frequency of TX path"""
        return self._get_iio_attr("altvoltage1", "frequency", True)

    @tx_lo.setter
    def tx_lo(self, value):
        self._set_iio_attr("altvoltage1", "frequency", True, value)


class ad9364(ad9361):
    """ AD9364 Transceiver """

    _rx_channel_names = ["voltage0", "voltage1"]
    _tx_channel_names = ["voltage0", "voltage1"]


class ad9363(ad9361):
    """ AD9363 Transceiver """

    pass


class Pluto(ad9364):
    """ PlutoSDR Evaluation Platform """

    _device_name = "PlutoSDR"
    _uri_auto = "ip:pluto.local"
