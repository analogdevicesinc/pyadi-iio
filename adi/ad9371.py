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
from adi.jesd import jesd
from adi.obs import obs
from adi.rx_tx import rx_tx


class ad9371(rx_tx, context_manager):
    """ AD9371 Transceiver """

    _complex_data = True
    _rx_channel_names = ["voltage0_i", "voltage0_q", "voltage1_i", "voltage1_q"]
    _tx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _obs_channel_names = ["voltage0_i", "voltage0_q"]
    _device_name = ""

    def __init__(
        self, uri="", username="root", password="analog", disable_jesd_control=False
    ):
        """Initialize AD9371 interface class.
        Args:
            uri (str): URI of target platform with AD9371
            username (str): SSH username for target board. Required for JESD monitoring
            password (str): SSH password for target board. Required for JESD monitoring
            disable_jesd_control (bool): Disable JESD status monitoring over SSH
        """
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ad9371-phy")
        self._rxadc = self._ctx.find_device("axi-ad9371-rx-hpc")
        self._rxobs = self._ctx.find_device("axi-ad9371-rx-obs-hpc")
        self._txdac = self._ctx.find_device("axi-ad9371-tx-hpc")

        if not disable_jesd_control and jesd:
            self._jesd = jesd(uri, username=username, password=password)

        rx_tx.__init__(self)

        self.obs = obs(self._ctx, self._rxobs, self._obs_channel_names)

    @property
    def ensm_mode(self):
        """ensm_mode: Enable State Machine State Allows real time control over
        the current state of the device. Options are: radio_on, radio_off"""
        return self._get_iio_dev_attr_str("ensm_mode")

    @ensm_mode.setter
    def ensm_mode(self, value):
        self._set_iio_dev_attr_str("ensm_mode", value)

    @property
    def gain_control_mode(self):
        """gain_control_mode: Mode of receive path AGC. Options are:
        automatic, hybrid, manual"""
        return self._get_iio_attr_str("voltage0", "gain_control_mode", False)

    @gain_control_mode.setter
    def gain_control_mode(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def rx_quadrature_tracking_en_chan0(self):
        """Enable Quadrature tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "quadrature_tracking_en", False)

    @rx_quadrature_tracking_en_chan0.setter
    def rx_quadrature_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "quadrature_tracking_en", False, value)

    @property
    def rx_quadrature_tracking_en_chan1(self):
        """Enable Quadrature tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "quadrature_tracking_en", False)

    @rx_quadrature_tracking_en_chan1.setter
    def rx_quadrature_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "quadrature_tracking_en", False, value)

    @property
    def rx_hardwaregain_chan0(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain_chan0.setter
    def rx_hardwaregain_chan0(self, value):
        if self.gain_control_mode == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def rx_hardwaregain_chan1(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False)

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        if self.gain_control_mode == "manual":
            self._set_iio_attr("voltage1", "hardwaregain", False, value)

    @property
    def rx_temp_comp_gain_chan0(self):
        """rx_temp_comp_gain_chan0: """
        return self._get_iio_attr("voltage0", "temp_comp_gain", False)

    @rx_temp_comp_gain_chan0.setter
    def rx_temp_comp_gain_chan0(self, value):
        self._set_iio_attr("voltage0", "temp_comp_gain", False, value)

    @property
    def rx_temp_comp_gain_chan1(self):
        """rx_temp_comp_gain_chan1: """
        return self._get_iio_attr("voltage1", "temp_comp_gain", False)

    @rx_temp_comp_gain_chan1.setter
    def rx_temp_comp_gain_chan1(self, value):
        self._set_iio_attr("voltage1", "temp_comp_gain", False, value)

    @property
    def tx_quadrature_tracking_en_chan0(self):
        """Enable Quadrature tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "quadrature_tracking_en", True)

    @tx_quadrature_tracking_en_chan0.setter
    def tx_quadrature_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "quadrature_tracking_en", True, value)

    @property
    def tx_quadrature_tracking_en_chan1(self):
        """Enable Quadrature tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "quadrature_tracking_en", True)

    @tx_quadrature_tracking_en_chan1.setter
    def tx_quadrature_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "quadrature_tracking_en", True, value)

    @property
    def tx_hardwaregain_chan0(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 0"""
        return self._get_iio_attr("voltage0", "hardwaregain", True)

    @tx_hardwaregain_chan0.setter
    def tx_hardwaregain_chan0(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value)

    @property
    def tx_hardwaregain_chan1(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 1"""
        return self._get_iio_attr("voltage1", "hardwaregain", True)

    @tx_hardwaregain_chan1.setter
    def tx_hardwaregain_chan1(self, value):
        self._set_iio_attr("voltage1", "hardwaregain", True, value)

    @property
    def rx_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False)

    @property
    def tx_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True)

    @property
    def rx_enable_dec8(self):
        """rx_enable_dec8: Enable x8 decimation filter in RX path"""
        avail = self._get_iio_attr_str(
            "voltage0_i", "sampling_frequency_available", False, self._rxadc
        )
        avail = avail.strip().split(" ")
        val = self._get_iio_attr_str(
            "voltage0_i", "sampling_frequency", False, self._rxadc
        )
        return val == avail[1]

    @rx_enable_dec8.setter
    def rx_enable_dec8(self, value):
        avail = self._get_iio_attr_str(
            "voltage0_i", "sampling_frequency_available", False, self._rxadc
        )
        avail = sorted(avail.strip().split(" "))
        val = int(avail[1] if value else avail[0])
        self._set_iio_attr("voltage0_i", "sampling_frequency", False, val, self._rxadc)

    @property
    def tx_enable_int8(self):
        """tx_enable_int8: Enable x8 interpolation filter in TX path"""
        avail = self._get_iio_attr_str(
            "voltage0", "sampling_frequency_available", True, self._txdac
        )
        avail = avail.strip().split(" ")
        val = self._get_iio_attr_str(
            "voltage0", "sampling_frequency", True, self._txdac
        )
        return val == avail[1]

    @tx_enable_int8.setter
    def tx_enable_int8(self, value):
        avail = self._get_iio_attr_str(
            "voltage0", "sampling_frequency_available", True, self._txdac
        )
        avail = sorted(avail.strip().split(" "))
        val = int(avail[1] if value else avail[0])
        self._set_iio_attr("voltage0", "sampling_frequency", True, val, self._txdac)

    @property
    def rx_sample_rate(self):
        """rx_sample_rate: Sample rate RX path in samples per second
            This value will reflect the correct value when 8x decimator is enabled
        """
        dec = 8 if self.rx_enable_dec8 else 1
        return self._get_iio_attr("voltage0", "sampling_frequency", False) / dec

    @property
    def orx_sample_rate(self):
        """orx_sample_rate: Sample rate ORX path in samples per second
            This value will reflect the correct value when 8x decimator is enabled
        """
        dec = 8 if self.rx_enable_dec8 else 1
        return self._get_iio_attr("voltage2", "sampling_frequency", False) / dec

    @property
    def tx_sample_rate(self):
        """tx_sample_rate: Sample rate TX path in samples per second
            This value will reflect the correct value when 8x interpolator is enabled
        """
        dec = 8 if self.tx_enable_int8 else 1
        return self._get_iio_attr("voltage0", "sampling_frequency", True) / dec

    @property
    def rx_lo(self):
        """rx_lo: Carrier frequency of RX path"""
        return self._get_iio_attr("altvoltage0", "RX_LO_frequency", True)

    @rx_lo.setter
    def rx_lo(self, value):
        self._set_iio_attr("altvoltage0", "RX_LO_frequency", True, value)

    @property
    def tx_lo(self):
        """tx_lo: Carrier frequency of TX path"""
        return self._get_iio_attr("altvoltage1", "TX_LO_frequency", True)

    @tx_lo.setter
    def tx_lo(self, value):
        self._set_iio_attr("altvoltage1", "TX_LO_frequency", True, value)

    @property
    def sn_lo(self):
        """sn_lo: Carrier frequency of Sniffer/ORx path"""
        return self._get_iio_attr("altvoltage2", "RX_SN_LO_frequency", True)

    @sn_lo.setter
    def sn_lo(self, value):
        self._set_iio_attr("altvoltage2", "RX_SN_LO_frequency", True, value)

    @property
    def obs_gain_control_mode(self):
        """obs_gain_control_mode: Mode of Obs/Sniffer receive path AGC. Options are:
        automatic, hybrid, manual"""
        return self._get_iio_attr_str("voltage2", "gain_control_mode", False)

    @obs_gain_control_mode.setter
    def obs_gain_control_mode(self, value):
        self._set_iio_attr("voltage2", "gain_control_mode", False, value)

    @property
    def obs_hardwaregain(self):
        """obs_hardwaregain: Gain applied to Obs/Sniffer receive path chan0. Only applicable when
        obs_gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage2", "hardwaregain", False)

    @obs_hardwaregain.setter
    def obs_hardwaregain(self, value):
        if self.obs_gain_control_mode == "manual":
            self._set_iio_attr("voltage2", "hardwaregain", False, value)

    @property
    def obs_temp_comp_gain(self):
        """obs_temp_comp_gain: """
        return self._get_iio_attr("voltage2", "temp_comp_gain", False)

    @obs_temp_comp_gain.setter
    def obs_temp_comp_gain(self, value):
        self._set_iio_attr("voltage2", "temp_comp_gain", False, value)

    @property
    def obs_quadrature_tracking_en(self):
        """Enable Quadrature tracking calibration for OBS chan0"""
        return self._get_iio_attr("voltage2", "quadrature_tracking_en", False)

    @obs_quadrature_tracking_en.setter
    def obs_quadrature_tracking_en(self, value):
        self._set_iio_attr("voltage2", "quadrature_tracking_en", False, value)

    @property
    def obs_rf_port_select(self):
        """obs_rf_port_select: Observation path source. Options are:

        - OFF - SnRx path is disabled
        - ORX1_TX_LO – SnRx operates in observation mode on ORx1 with Tx LO synthesizer
        - ORX2_TX_LO – SnRx operates in observation mode on ORx2 with Tx LO synthesizer
        - INTERNALCALS – enables scheduled Tx calibrations while using SnRx path. The enableTrackingCals function needs to be called in RADIO_OFF state. It sets the calibration mask, which the scheduler will later use to schedule the desired calibrations. This command is issued in RADIO_OFF. Once the AD9371 moves to RADIO_ON state, the internal scheduler will use the enabled calibration mask to schedule calibrations whenever possible, based on the state of the transceiver. The Tx calibrations will not be scheduled until INTERNALCALS is selected and the Tx calibrations are enabled in the cal mask.
        - OBS_SNIFFER – SnRx operates in sniffer mode with latest selected Sniffer Input – for hardware pin control operation. In pin mode, the GPIO pins designated for ORX_MODE would select SNIFFER mode. Then MYKONOS_setSnifferChannel function would choose the channel.
        - ORX1_SN_LO – SnRx operates in observation mode on ORx1 with SNIFFER LO synthesizer
        - ORX2_SN_LO – SnRx operates in observation mode on ORx2 with SNIFFER LO synthesizer
        - SN_A – SnRx operates in sniffer mode on SnRxA with SNIFFER LO synthesizer
        - SN_B – SnRx operates in sniffer mode on SnRxB with SNIFFER LO synthesizer
        - SN_C – SnRx operates in sniffer mode on SnRxC with SNIFFER LO synthesizer

        """
        return self._get_iio_attr_str("voltage2", "rf_port_select", False)

    @obs_rf_port_select.setter
    def obs_rf_port_select(self, value):
        self._set_iio_attr("voltage2", "rf_port_select", False, value)

    @property
    def jesd204_statuses(self):
        return self._jesd.get_all_statuses()
