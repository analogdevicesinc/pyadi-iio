# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.adrv9009_zu11eg import adrv9009_zu11eg


class adrv9009_zu11eg_fmcomms8(adrv9009_zu11eg):
    """ ADRV9009-ZU11EG System-On-Module + FMCOMMS8

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

    def __init__(self, uri="", jesd_monitor=False, jesd=None):
        adrv9009_zu11eg.__init__(self, uri=uri, jesd_monitor=jesd_monitor, jesd=jesd)
        self._ctrl_c = self._ctx.find_device("adrv9009-phy-c")
        self._ctrl_d = self._ctx.find_device("adrv9009-phy-d")
        self._clock_chip_fmc = self._ctx.find_device("hmc7044-fmc")

    def mcs_chips(self):
        """mcs_chips: MCS Synchronize all four transceivers """
        try:
            _ = self.jesd204_fsm_ctrl
            # We're JESD204-fsm enabled - do nothing
        except:  # noqa: E722
            # Turn off continuous SYSREF, and enable GPI SYSREF request
            self._clock_chip_carrier.reg_write(0x5A, 0)
            chips = [self._ctrl, self._ctrl_b, self._ctrl_c, self._ctrl_d]
            for i in range(12):
                for chip in chips:
                    try:
                        self._set_iio_dev_attr_str("multichip_sync", i, chip)
                    except OSError:
                        pass

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
