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

from adi.adrv9009 import adrv9009


class adrv9009_zu11eg(adrv9009):
    """ ADRV9009-ZU11EG System-On-Module

    parameters:
        uri: type=string
            URI of context with ADRV9009-ZU11EG
        jesd_monitor: type=boolean
            Boolean flag to enable JESD monitoring. jesd input is
            ignored otherwise.
        jesd: type=adi.jesd
            JESD object associated with ADRV9009-ZU11EG
    """

    _rx_channel_names = [
        "voltage0_i",
        "voltage0_q",
        "voltage1_i",
        "voltage1_q",
        "voltage2_i",
        "voltage2_q",
        "voltage3_i",
        "voltage3_q",
    ]
    _tx_channel_names = [
        "voltage0",
        "voltage1",
        "voltage2",
        "voltage3",
        "voltage4",
        "voltage5",
        "voltage6",
        "voltage7",
    ]
    _device_name = ""

    def __init__(self, uri="", jesd_monitor=False, jesd=None):

        adrv9009.__init__(self, uri=uri, jesd_monitor=jesd_monitor, jesd=jesd)
        self._ctrl_b = self._ctx.find_device("adrv9009-phy-b")
        self._clock_chip = self._ctx.find_device("hmc7044")
        self._clock_chip_carrier = self._ctx.find_device("hmc7044-car")
        # Used for multi-som sync
        self._clock_chip_ext = self._ctx.find_device("hmc7044-ext")

    def mcs_chips(self):
        """mcs_chips: MCS Synchronize both transceivers """
        try:
            _ = self.jesd204_fsm_ctrl
            # We're JESD204-fsm enabled - do nothing
        except:  # noqa: E722
            # Turn off continuous SYSREF, and enable GPI SYSREF request
            self._clock_chip.reg_write(0x5A, 0)
            for i in range(12):
                try:
                    self._set_iio_dev_attr_str("multichip_sync", i)
                except OSError:
                    pass
                try:
                    self._set_iio_dev_attr_str("multichip_sync", i, self._ctrl_b)
                except OSError:
                    pass

    @property
    def frequency_hopping_mode_chip_b(self):
        """frequency_hopping_mode_chip_b: Set Frequency Hopping Mode"""
        return self._get_iio_attr(
            "TRX_LO", "frequency_hopping_mode", True, self._ctrl_b
        )

    @frequency_hopping_mode_chip_b.setter
    def frequency_hopping_mode_chip_b(self, value):
        self._set_iio_attr(
            "TRX_LO", "frequency_hopping_mode", True, value, self._ctrl_b
        )

    @property
    def frequency_hopping_mode_en_chip_b(self):
        """frequency_hopping_mode_en: Enable Frequency Hopping Mode"""
        return self._get_iio_attr(
            "TRX_LO", "frequency_hopping_mode_enable", True, self._ctrl_b
        )

    @frequency_hopping_mode_en_chip_b.setter
    def frequency_hopping_mode_en_chip_b(self, value):
        self._set_iio_attr(
            "TRX_LO", "frequency_hopping_mode_enable", True, value, self._ctrl_b
        )

    @property
    def calibrate_rx_phase_correction_en_chip_b(self):
        """calibrate_rx_phase_correction_en: Enable RX Phase Correction Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_phase_correction_en", self._ctrl_b)

    @calibrate_rx_phase_correction_en_chip_b.setter
    def calibrate_rx_phase_correction_en_chip_b(self, value):
        self._set_iio_dev_attr_str(
            "calibrate_rx_phase_correction_en", value, self._ctrl_b
        )

    @property
    def calibrate_rx_qec_en_chip_b(self):
        """calibrate_rx_qec_en_chip_b: Enable RX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_qec_en", self._ctrl_b)

    @calibrate_rx_qec_en_chip_b.setter
    def calibrate_rx_qec_en_chip_b(self, value):
        self._set_iio_dev_attr_str("calibrate_rx_qec_en", value, self._ctrl_b)

    @property
    def calibrate_tx_qec_en_chip_b(self):
        """calibrate_tx_qec_en_chip_b: Enable TX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_tx_qec_en", self._ctrl_b)

    @calibrate_tx_qec_en_chip_b.setter
    def calibrate_tx_qec_en_chip_b(self, value):
        self._set_iio_dev_attr_str("calibrate_tx_qec_en", value, self._ctrl_b)

    @property
    def calibrate_chip_b(self):
        """calibrate_chip_b: Trigger Calibration"""
        return self._get_iio_dev_attr("calibrate", self._ctrl_b)

    @calibrate_chip_b.setter
    def calibrate_chip_b(self, value):
        self._set_iio_dev_attr_str("calibrate", value, self._ctrl_b)

    @property
    def gain_control_mode_chan0_chip_b(self):
        """gain_control_mode_chan0_chip_b: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage0", "gain_control_mode", False, self._ctrl_b
        )

    @gain_control_mode_chan0_chip_b.setter
    def gain_control_mode_chan0_chip_b(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value, self._ctrl_b)

    @property
    def gain_control_mode_chan1_chip_b(self):
        """gain_control_mode_chan1_chip_b: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage1", "gain_control_mode", False, self._ctrl_b
        )

    @gain_control_mode_chan1_chip_b.setter
    def gain_control_mode_chan1_chip_b(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value, self._ctrl_b)

    @property
    def rx_hardwaregain_chan0_chip_b(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False, self._ctrl_b)

    @rx_hardwaregain_chan0_chip_b.setter
    def rx_hardwaregain_chan0_chip_b(self, value):
        if self.gain_control_mode_chan0_chip_b == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value, self._ctrl_b)

    @property
    def rx_hardwaregain_chan1_chip_b(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False, self._ctrl_b)

    @rx_hardwaregain_chan1_chip_b.setter
    def rx_hardwaregain_chan1_chip_b(self, value):
        if self.gain_control_mode_chan1_chip_b == "manual":
            self._set_iio_attr("voltage1", "hardwaregain", False, value, self._ctrl_b)

    @property
    def tx_hardwaregain_chan0_chip_b(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 0"""
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl_b)

    @tx_hardwaregain_chan0_chip_b.setter
    def tx_hardwaregain_chan0_chip_b(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value, self._ctrl_b)

    @property
    def tx_hardwaregain_chan1_chip_b(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 1"""
        return self._get_iio_attr("voltage1", "hardwaregain", True, self._ctrl_b)

    @tx_hardwaregain_chan1_chip_b.setter
    def tx_hardwaregain_chan1_chip_b(self, value):
        self._set_iio_attr("voltage1", "hardwaregain", True, value, self._ctrl_b)

    @property
    def rx_rf_bandwidth_chip_b(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False, self._ctrl_b)

    @property
    def tx_rf_bandwidth_chip_b(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True, self._ctrl_b)

    @property
    def rx_sample_rate_chip_b(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._ctrl_b)

    @property
    def tx_sample_rate_chip_b(self):
        """tx_sample_rate: Sample rate TX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._ctrl_b)

    @property
    def trx_lo_chip_b(self):
        """trx_lo: Carrier frequency of TX and RX path"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl_b)

    @trx_lo_chip_b.setter
    def trx_lo_chip_b(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl_b)
