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


class ad9364(rx_tx, context_manager):
    """ AD9364 Transceiver """

    _complex_data = True
    _rx_channel_names = ["voltage0", "voltage1"]
    _tx_channel_names = ["voltage0", "voltage1"]
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
    def gain_control_mode_chan0(self):
        """gain_control_mode_chan0: Mode of receive path AGC. Options are:
        slow_attack, fast_attack, manual"""
        return self._get_iio_attr_str("voltage0", "gain_control_mode", False)

    @gain_control_mode_chan0.setter
    def gain_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain_chan0(self):
        """rx_hardwaregain_chan0: Gain applied to RX path. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain_chan0.setter
    def rx_hardwaregain_chan0(self, value):
        if self.gain_control_mode_chan0 == "manual":
            self._set_iio_attr_float("voltage0", "hardwaregain", False, value)

    @property
    def tx_hardwaregain_chan0(self):
        """tx_hardwaregain_chan0: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage0", "hardwaregain", True)

    @tx_hardwaregain_chan0.setter
    def tx_hardwaregain_chan0(self, value):
        self._set_iio_attr_float("voltage0", "hardwaregain", True, value)

    @property
    def rx_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False)

    @rx_rf_bandwidth.setter
    def rx_rf_bandwidth(self, value):
        self._set_iio_attr_int("voltage0", "rf_bandwidth", False, value)

    @property
    def tx_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True)

    @tx_rf_bandwidth.setter
    def tx_rf_bandwidth(self, value):
        self._set_iio_attr_int("voltage0", "rf_bandwidth", True, value)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, rate):
        if rate < 521e3:
            raise ValueError(
                "Error: Does not currently support sample rates below 521e3"
            )

        # The following was converted from ad9361_set_bb_rate() in libad9361-iio
        # fmt: off
        if (rate <= 20000000):
            dec = 4
            fir = [
                -15, -27, -23, -6, 17, 33, 31, 9, -23, -47, -45, -13, 34, 69,
                67, 21, -49, -102, -99, -32, 69, 146, 143, 48, -96, -204, -200,
                -69, 129, 278, 275, 97, -170, -372, -371, -135, 222, 494, 497,
                187, -288, -654, -665, -258, 376, 875, 902, 363, -500, -1201,
                -1265, -530, 699, 1748, 1906, 845, -1089, -2922, -3424, -1697,
                2326, 7714, 12821, 15921, 15921, 12821, 7714, 2326, -1697,
                -3424, -2922, -1089, 845, 1906, 1748, 699, -530, -1265, -1201,
                -500, 363, 902, 875, 376, -258, -665, -654, -288, 187, 497,
                494, 222, -135, -371, -372, -170, 97, 275, 278, 129, -69, -200,
                -204, -96, 48, 143, 146, 69, -32, -99, -102, -49, 21, 67, 69,
                34, -13, -45, -47, -23, 9, 31, 33, 17, -6, -23, -27, -15
            ]
            taps = 128
        elif (rate <= 40000000):
            dec = 2
            fir = [
                -0, 0, 1, -0, -2, 0, 3, -0, -5, 0, 8, -0, -11, 0, 17, -0, -24,
                0, 33, -0, -45, 0, 61, -0, -80, 0, 104, -0, -134, 0, 169, -0,
                -213, 0, 264, -0, -327, 0, 401, -0, -489, 0, 595, -0, -724, 0,
                880, -0, -1075, 0, 1323, -0, -1652, 0, 2114, -0, -2819, 0,
                4056, -0, -6883, 0, 20837, 32767, 20837, 0, -6883, -0, 4056, 0,
                -2819, -0, 2114, 0, -1652, -0, 1323, 0, -1075, -0, 880, 0,
                -724, -0, 595, 0, -489, -0, 401, 0, -327, -0, 264, 0, -213, -0,
                169, 0, -134, -0, 104, 0, -80, -0, 61, 0, -45, -0, 33, 0, -24,
                -0, 17, 0, -11, -0, 8, 0, -5, -0, 3, 0, -2, -0, 1, 0, -0, 0
            ]
            taps = 128
        elif (rate <= 53333333):
            dec = 2
            fir = [
                -4, 0, 8, -0, -14, 0, 23, -0, -36, 0, 52, -0, -75, 0, 104, -0,
                -140, 0, 186, -0, -243, 0, 314, -0, -400, 0, 505, -0, -634, 0,
                793, -0, -993, 0, 1247, -0, -1585, 0, 2056, -0, -2773, 0, 4022,
                -0, -6862, 0, 20830, 32767, 20830, 0, -6862, -0, 4022, 0,
                -2773, -0, 2056, 0, -1585, -0, 1247, 0, -993, -0, 793, 0, -634,
                -0, 505, 0, -400, -0, 314, 0, -243, -0, 186, 0, -140, -0, 104,
                0, -75, -0, 52, 0, -36, -0, 23, 0, -14, -0, 8, 0, -4, 0
            ]
            taps = 96
        else:
            dec = 2
            fir = [
                -58, 0, 83, -0, -127, 0, 185, -0, -262, 0, 361, -0, -488, 0,
                648, -0, -853, 0, 1117, -0, -1466, 0, 1954, -0, -2689, 0, 3960,
                -0, -6825, 0, 20818, 32767, 20818, 0, -6825, -0, 3960, 0,
                -2689, -0, 1954, 0, -1466, -0, 1117, 0, -853, -0, 648, 0, -488,
                -0, 361, 0, -262, -0, 185, 0, -127, -0, 83, 0, -58, 0
            ]
            taps = 64
        # fmt: on
        current_rate = self._get_iio_attr("voltage0", "sampling_frequency", False)

        if self._get_iio_attr("out", "voltage_filter_fir_en", False):
            if current_rate <= (25000000 // 12):
                self._set_iio_attr("voltage0", "sampling_frequency", False, 3000000)
            self._set_iio_attr("out", "voltage_filter_fir_en", False, 0)

        # Assemble FIR filter config string
        fir_config_string = ""
        fir_config_string += "RX 3 GAIN -6 DEC " + str(dec) + "\n"
        fir_config_string += "TX 3 GAIN 0 INT " + str(dec) + "\n"
        for i in range(taps):
            fir_config_string += str(fir[i]) + "," + str(fir[i]) + "\n"
        fir_config_string += "\n"
        self._set_iio_dev_attr_str("filter_fir_config", fir_config_string)

        if rate <= (25000000 // 12):
            readbuf = self._get_iio_dev_attr_str("tx_path_rates")
            dacrate = int(readbuf.split(" ")[1].split(":")[1])
            txrate = int(readbuf.split(" ")[5].split(":")[1])
            max_rate = (dacrate // txrate) * 16
            if max_rate < taps:
                self._set_iio_attr("voltage0", "sampling_frequency", False, 3000000)
            self._set_iio_attr("out", "voltage_filter_fir_en", False, 1)
            self._set_iio_attr("voltage0", "sampling_frequency", False, rate)
        else:
            self._set_iio_attr("voltage0", "sampling_frequency", False, rate)
            self._set_iio_attr("out", "voltage_filter_fir_en", False, 1)

    @property
    def rx_lo(self):
        """rx_lo: Carrier frequency of RX path"""
        return self._get_iio_attr("altvoltage0", "frequency", True)

    @rx_lo.setter
    def rx_lo(self, value):
        self._set_iio_attr_int("altvoltage0", "frequency", True, value)

    @property
    def tx_lo(self):
        """tx_lo: Carrier frequency of TX path"""
        return self._get_iio_attr("altvoltage1", "frequency", True)

    @tx_lo.setter
    def tx_lo(self, value):
        self._set_iio_attr_int("altvoltage1", "frequency", True, value)


class ad9361(ad9364):
    """ AD9361 Transceiver """

    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _tx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]

    @property
    def gain_control_mode_chan1(self):
        """gain_control_mode_chan1: Mode of receive path AGC. Options are:
        slow_attack, fast_attack, manual"""
        return self._get_iio_attr_str("voltage1", "gain_control_mode", False)

    @gain_control_mode_chan1.setter
    def gain_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain_chan1(self):
        """rx_hardwaregain_chan1: Gain applied to RX path. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False)

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        if self.gain_control_mode_chan1 == "manual":
            self._set_iio_attr_float("voltage1", "hardwaregain", False, value)

    @property
    def tx_hardwaregain_chan1(self):
        """tx_hardwaregain_chan1: Attenuation applied to TX path"""
        return self._get_iio_attr("voltage1", "hardwaregain", True)

    @tx_hardwaregain_chan1.setter
    def tx_hardwaregain_chan1(self, value):
        self._set_iio_attr_float("voltage1", "hardwaregain", True, value)


class ad9363(ad9361):
    """ AD9363 Transceiver """

    pass


class Pluto(ad9364):
    """ PlutoSDR Evaluation Platform """

    _device_name = "PlutoSDR"
    _uri_auto = "ip:pluto.local"

    def __repr__(self):
        retstr = f"""Pluto(uri="{self.uri}") object "{self._device_name}" with following key properties:

rx_lo:                   {self.rx_lo / 1000000:<12} MHz, Carrier frequency of RX path
rx_hardwaregain_chan0    {self.rx_hardwaregain_chan0:<12} dB, Gain applied to RX path. Only applicable when gain_control_mode is set to 'manual'
rx_rf_bandwidth:         {self.rx_rf_bandwidth / 1000000:<12} MHz, Bandwidth of front-end analog filter of RX path
gain_control_mode_chan0: {self.gain_control_mode_chan0:<12} Receive path AGC Options: slow_attack, fast_attack, manual

tx_lo:                   {self.tx_lo / 1000000:<12} MHz, Carrier frequency of TX path
tx_hardwaregain_chan0:   {self.tx_hardwaregain_chan0:<12} dB, Attenuation applied to TX path
tx_rf_bandwidth:         {self.tx_rf_bandwidth / 1000000:<12} MHz, Bandwidth of front-end analog filter of TX path
tx_cyclic_buffer:        {self.tx_cyclic_buffer:<12} Toggles cyclic buffer

filter:                  {str(self.filter):<12} FIR filter file
sample_rate:             {self.sample_rate / 1000000:<12} MSPS, Sample rate RX and TX paths
loopback:                {self.loopback:<12} 0=Disabled, 1=Digital, 2=RF

"""
        return retstr
