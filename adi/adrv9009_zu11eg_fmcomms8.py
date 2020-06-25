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

from adi.adrv9009_zu11eg import adrv9009_zu11eg
import time


class adrv9009_zu11eg_fmcomms8(adrv9009_zu11eg):
    """ ADRV9009-ZU11EG System-On-Module + FMCOMMS8"""

    _rx_channel_names = [
        "voltage0_i",
        "voltage0_q",
        "voltage1_i",
        "voltage1_q",
        "voltage2_i",
        "voltage2_q",
        "voltage3_i",
        "voltage3_q",
        "voltage4_i",
        "voltage4_q",
        "voltage5_i",
        "voltage5_q",
        "voltage6_i",
        "voltage6_q",
        "voltage7_i",
        "voltage7_q",
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
        "voltage8",
        "voltage9",
        "voltage10",
        "voltage11",
        "voltage12",
        "voltage13",
        "voltage14",
        "voltage15",
    ]
    _device_name = ""
    _sync_init = False

    def __init__(self, uri=""):
        adrv9009_zu11eg.__init__(self, uri=uri)
        self._ctrl_c = self._ctx.find_device("adrv9009-phy-c")
        self._ctrl_d = self._ctx.find_device("adrv9009-phy-d")
        self._clock_chip_fmc = self._ctx.find_device("hmc7044-fmc")

    def clock_chip_reset(self):
        self._clock_chip_carrier.reg_write(0x5, 0x4A)
        self._clock_chip_carrier.reg_write(0x1, 0x1)
        time.sleep(1)
        self._clock_chip_carrier.reg_write(0x1, 0x0)
        self._clock_chip.reg_write(0x5, 0x43)
        self._clock_chip.reg_write(0x5A, 0x7)
        self._clock_chip.reg_write(0x1, 0x1)
        time.sleep(1)
        self._clock_chip.reg_write(0x1, 0x60)
        self._clock_chip_fmc.reg_write(0x5, 0x43)
        self._clock_chip_fmc.reg_write(0x5A, 0x7)
        self._clock_chip_fmc.reg_write(0x1, 0x1)
        time.sleep(1)
        self._clock_chip_fmc.reg_write(0x1, 0x60)

    def reinitialize_trx(self):
        chips = [self._ctrl, self._ctrl_b, self._ctrl_c, self._ctrl_d]
        for chip in chips:
            chip._set_iio_debug_attr_str("initialize", "1", chip)

    def init(self):
        self._clock_chip.reg_write(0x5A, 0x04)
        self._clock_chip_fmc.reg_write(0x5A, 0x04)

    def unsync(self):
        # sleep -> wakeup
        self._clock_chip.reg_write(0x01, 0x61)
        self._clock_chip_fmc.reg_write(0x01, 0x01)
        self._clock_chip_carrier.reg_write(0x01, 0x61)
        time.sleep(0.1)
        self._clock_chip_carrier.reg_write(0x01, 0x60)
        time.sleep(0.1)
        self._clock_chip.reg_write(0x01, 0x60)
        time.sleep(0.1)
        self._clock_chip_fmc.reg_write(0x01, 0x60)
        time.sleep(0.1)

    def hmc7044_setup(self):
        # CLK2 sync pin mode disabled to avoid false triggering
        # needs to be enabled if there is another master in the system
        self._clock_chip_carrier.reg_write(0x05, 0x02)

        # CLK3 sync pin mode as SYNC
        self._clock_chip.reg_write(0x05, 0x43)
        # CLK3 sync pin mode as SYNC
        self._clock_chip_fmc.reg_write(0x05, 0x43)

        # restart request for all 7044
        self._clock_chip.reg_write(0x01, 0x62)
        self._clock_chip_fmc.reg_write(0x01, 0x62)  # INTREBARE
        self._clock_chip_carrier.reg_write(0x01, 0x62)

        # restart from top of the clocking tree
        time.sleep(0.1)
        self._clock_chip_carrier.reg_write(0x1, 0x60)
        time.sleep(0.1)
        self._clock_chip.reg_write(0x1, 0x60)
        time.sleep(0.1)
        self._clock_chip_fmc.reg_write(0x1, 0x60)
        time.sleep(0.1)

    def clock_sync(self):
        # Sync pulse is always requested to the master clk and propagates to the system
        # once a level has been synced, sync pin mode needs to be changed to pulsor
        # Reseed request to clk2 -----> syncs the output of CLK2
        self._clock_chip_carrier.reg_write(0x01, 0xE0)
        self._clock_chip_carrier.reg_write(0x01, 0x60)
        time.sleep(0.1)
        # pulse request to CLK2----> syncs the outputs of CLK3
        self._clock_chip_carrier.attrs["sysref_request"] = 1
        time.sleep(0.1)

        # CLK3 sync pin mode as Pulsor so it doesn't resync on next pulse
        self._clock_chip.reg_write(0x05, 0x83)
        self._clock_chip_fmc.reg_write(0x05, 0x83)

    def mcs_chips(self):
        """mcs_chips: MCS Synchronize all four transceivers """
        # Turn off continuous SYSREF, and enable GPI SYSREF request

        # 16 pulses on pulse generator request
        self._clock_chip.reg_write(0x5A, 5)
        self._clock_chip_fmc.reg_write(0x5A, 5)

        sysref_request_steps = [2, 5, 7, 10]
        chips = [self._ctrl, self._ctrl_b, self._ctrl_c, self._ctrl_d]
        for i in range(12):
            if i in sysref_request_steps:
                self._clock_chip_carrier.attrs["sysref_request"] = 1
                continue

            for chip in chips:
                self._set_iio_dev_attr_str("multichip_sync", i, chip)

        time.sleep(0.1)
        self._clock_chip_carrier.attrs["sysref_request"] = 1
        self._clock_chip.reg_write(0x5A, 1)
        self._clock_chip_fmc.reg_write(0x5A, 1)

    def calibrate_rx_phase_correction(self):
        for chip in [self._ctrl, self._ctrl_b, self._ctrl_c, self._ctrl_d]:
            chip.attrs["calibrate_rx_phase_correction_en"] = 1
            chip.attrs["calibrate"] = 1

        time.sleep(0.1)
        self._clock_chip_carrier.attrs["sysref_request"] = 1
        time.sleep(1)

    def rx_synced(self):
        if not self._sync_init:
            self.init()
            self.unsync()
            self.hmc7044_setup()
            self.clock_sync()
            for i in range(3):
                try:
                    self.mcs_chips()
                    break
                except Exception as ex:
                    print("Got Exception... trying MCS again", ex)
                try:
                    self.mcs_chips()
                    break
                except Exception as ex:
                    print("Got Exception again... reseting clocks and transceivers", ex)
                if i >= 2:
                    raise Exception("Too many retries failed")
                self.clock_chip_reset()
                self.reinitialize_trx()

            self.calibrate_rx_phase_correction()
            self._sync_init = True
        return self.rx()

    @property
    def calibrate_rx_phase_correction_en_chip_c(self):
        """calibrate_rx_phase_correction_en: Enable RX Phase Correction Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_phase_correction_en", self._ctrl_c)

    @calibrate_rx_phase_correction_en_chip_c.setter
    def calibrate_rx_phase_correction_en_chip_c(self, value):
        self._set_iio_dev_attr_str(
            "calibrate_rx_phase_correction_en", value, self._ctrl_c
        )

    @property
    def calibrate_rx_qec_en_chip_c(self):
        """calibrate_rx_qec_en_chip_c: Enable RX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_qec_en", self._ctrl_c)

    @calibrate_rx_qec_en_chip_c.setter
    def calibrate_rx_qec_en_chip_c(self, value):
        self._set_iio_dev_attr_str("calibrate_rx_qec_en", value, self._ctrl_c)

    @property
    def calibrate_tx_qec_en_chip_c(self):
        """calibrate_tx_qec_en_chip_c: Enable TX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_tx_qec_en", self._ctrl_c)

    @calibrate_tx_qec_en_chip_c.setter
    def calibrate_tx_qec_en_chip_c(self, value):
        self._set_iio_dev_attr_str("calibrate_tx_qec_en", value, self._ctrl_c)

    @property
    def calibrate_chip_c(self):
        """calibrate_chip_c: Trigger Calibration"""
        return self._get_iio_dev_attr("calibrate", self._ctrl_c)

    @calibrate_chip_c.setter
    def calibrate_chip_c(self, value):
        self._set_iio_dev_attr_str("calibrate", value, self._ctrl_c)

    @property
    def gain_control_mode_chan0_chip_c(self):
        """gain_control_mode_chan0_chip_c: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage0", "gain_control_mode", False, self._ctrl_c
        )

    @gain_control_mode_chan0_chip_c.setter
    def gain_control_mode_chan0_chip_c(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value, self._ctrl_c)

    @property
    def gain_control_mode_chan1_chip_c(self):
        """gain_control_mode_chan1_chip_c: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage1", "gain_control_mode", False, self._ctrl_c
        )

    @gain_control_mode_chan1_chip_c.setter
    def gain_control_mode_chan1_chip_c(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value, self._ctrl_c)

    @property
    def rx_hardwaregain_chan0_chip_c(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False, self._ctrl_c)

    @rx_hardwaregain_chan0_chip_c.setter
    def rx_hardwaregain_chan0_chip_c(self, value):
        if self.gain_control_mode_chan0_chip_c == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value, self._ctrl_c)

    @property
    def rx_hardwaregain_chan1_chip_c(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False, self._ctrl_c)

    @rx_hardwaregain_chan1_chip_c.setter
    def rx_hardwaregain_chan1_chip_c(self, value):
        if self.gain_control_mode_chan1_chip_c == "manual":
            self._set_iio_attr("voltage1", "hardwaregain", False, value, self._ctrl_c)

    @property
    def tx_hardwaregain_chan0_chip_c(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 0"""
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl_c)

    @tx_hardwaregain_chan0_chip_c.setter
    def tx_hardwaregain_chan0_chip_c(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value, self._ctrl_c)

    @property
    def tx_hardwaregain_chan1_chip_c(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 1"""
        return self._get_iio_attr("voltage1", "hardwaregain", True, self._ctrl_c)

    @tx_hardwaregain_chan1_chip_c.setter
    def tx_hardwaregain_chan1_chip_c(self, value):
        self._set_iio_attr("voltage1", "hardwaregain", True, value, self._ctrl_c)

    @property
    def rx_rf_bandwidth_chip_c(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False, self._ctrl_c)

    @property
    def tx_rf_bandwidth_chip_c(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True, self._ctrl_c)

    @property
    def rx_sample_rate_chip_c(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._ctrl_c)

    @property
    def tx_sample_rate_chip_c(self):
        """tx_sample_rate: Sample rate TX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._ctrl_c)

    @property
    def trx_lo_chip_c(self):
        """trx_lo: Carrier frequency of TX and RX path"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl_c)

    @trx_lo_chip_c.setter
    def trx_lo_chip_c(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl_c)

    # Chip d setter/getters

    @property
    def calibrate_rx_phase_correction_en_chip_d(self):
        """calibrate_rx_phase_correction_en: Enable RX Phase Correction Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_phase_correction_en", self._ctrl_d)

    @calibrate_rx_phase_correction_en_chip_d.setter
    def calibrate_rx_phase_correction_en_chip_d(self, value):
        self._set_iio_dev_attr_str(
            "calibrate_rx_phase_correction_en", value, self._ctrl_d
        )

    @property
    def calibrate_rx_qec_en_chip_d(self):
        """calibrate_rx_qec_en_chip_d: Enable RX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_qec_en", self._ctrl_d)

    @calibrate_rx_qec_en_chip_d.setter
    def calibrate_rx_qec_en_chip_d(self, value):
        self._set_iio_dev_attr_str("calibrate_rx_qec_en", value, self._ctrl_d)

    @property
    def calibrate_tx_qec_en_chip_d(self):
        """calibrate_tx_qec_en_chip_d: Enable TX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_tx_qec_en", self._ctrl_d)

    @calibrate_tx_qec_en_chip_d.setter
    def calibrate_tx_qec_en_chip_d(self, value):
        self._set_iio_dev_attr_str("calibrate_tx_qec_en", value, self._ctrl_d)

    @property
    def calibrate_chip_d(self):
        """calibrate_chip_d: Trigger Calibration"""
        return self._get_iio_dev_attr("calibrate", self._ctrl_d)

    @calibrate_chip_d.setter
    def calibrate_chip_d(self, value):
        self._set_iio_dev_attr_str("calibrate", value, self._ctrl_d)

    @property
    def gain_control_mode_chan0_chip_d(self):
        """gain_control_mode_chan0_chip_d: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage0", "gain_control_mode", False, self._ctrl_d
        )

    @gain_control_mode_chan0_chip_d.setter
    def gain_control_mode_chan0_chip_d(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value, self._ctrl_d)

    @property
    def gain_control_mode_chan1_chip_d(self):
        """gain_control_mode_chan1_chip_d: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str(
            "voltage1", "gain_control_mode", False, self._ctrl_d
        )

    @gain_control_mode_chan1_chip_d.setter
    def gain_control_mode_chan1_chip_d(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value, self._ctrl_d)

    @property
    def rx_hardwaregain_chan0_chip_d(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False, self._ctrl_d)

    @rx_hardwaregain_chan0_chip_d.setter
    def rx_hardwaregain_chan0_chip_d(self, value):
        if self.gain_control_mode_chan0_chip_d == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value, self._ctrl_d)

    @property
    def rx_hardwaregain_chan1_chip_d(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False, self._ctrl_d)

    @rx_hardwaregain_chan1_chip_d.setter
    def rx_hardwaregain_chan1_chip_d(self, value):
        if self.gain_control_mode_chan1_chip_d == "manual":
            self._set_iio_attr("voltage1", "hardwaregain", False, value, self._ctrl_d)

    @property
    def tx_hardwaregain_chan0_chip_d(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 0"""
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl_d)

    @tx_hardwaregain_chan0_chip_d.setter
    def tx_hardwaregain_chan0_chip_d(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", True, value, self._ctrl_d)

    @property
    def tx_hardwaregain_chan1_chip_d(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 1"""
        return self._get_iio_attr("voltage1", "hardwaregain", True, self._ctrl_d)

    @tx_hardwaregain_chan1_chip_d.setter
    def tx_hardwaregain_chan1_chip_d(self, value):
        self._set_iio_attr("voltage1", "hardwaregain", True, value, self._ctrl_d)

    @property
    def rx_rf_bandwidth_chip_d(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False, self._ctrl_d)

    @property
    def tx_rf_bandwidth_chip_d(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True, self._ctrl_d)

    @property
    def rx_sample_rate_chip_d(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False, self._ctrl_d)

    @property
    def tx_sample_rate_chip_d(self):
        """tx_sample_rate: Sample rate TX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._ctrl_d)

    @property
    def trx_lo_chip_d(self):
        """trx_lo: Carrier frequency of TX and RX path"""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl_d)

    @trx_lo_chip_d.setter
    def trx_lo_chip_d(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl_d)
