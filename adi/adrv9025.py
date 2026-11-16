# Copyright (C) 2019-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.jesd import jesd as jesdadi
from adi.obs import obs
from adi.rx_tx import rx_tx
from adi.sync_start import sync_start


class adrv9025(rx_tx, context_manager, sync_start):
    """ADRV9025 Transceiver

    parameters:
        uri: type=string
            URI of context with ADRV9025
        jesd_monitor: type=boolean
            Boolean flag to enable JESD monitoring. jesd input is
            ignored otherwise.
        jesd: type=adi.jesd
            JESD object associated with ADRV9025
    """

    _complex_data = True
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
        "voltage0_i",
        "voltage0_q",
        "voltage1_i",
        "voltage1_q",
        "voltage2_i",
        "voltage2_q",
        "voltage3_i",
        "voltage3_q",
    ]
    _device_name = ""

    def __init__(self, uri="", jesd_monitor=False, jesd=None):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("adrv9025-phy")
        self._rxadc = self._ctx.find_device("axi-adrv9025-rx-hpc")
        self._txdac = self._ctx.find_device("axi-adrv9025-tx-hpc")
        self._ctx.set_timeout(30000)  # Needed for loading profiles
        if jesdadi and jesd_monitor:
            self._jesd = jesd if jesd else jesdadi(uri=uri)
        rx_tx.__init__(self)

    # @property
    # def profile(self):
    #     """Load profile file. Provide path to profile file to attribute"""
    #     return self._get_iio_dev_attr("profile_config")

    # @profile.setter
    # def profile(self, value):
    #     with open(value, "r") as file:
    #         data = file.read()
    #     # Apply profiles in specific order if multiple phys found
    #     phys = [p for p in self.__dict__.keys() if "_ctrl" in p]
    #     phys = sorted(phys)
    #     for phy in phys[1:] + [phys[0]]:
    #         self._set_iio_dev_attr_str("profile_config", data, getattr(self, phy))

    @property
    def en0_rx(self):
        """en0_rx: Enable channel 0 RX"""
        return self._get_iio_attr("voltage0", "en", False)

    @en0_rx.setter
    def en0_rx(self, value):
        self._set_iio_attr("voltage0", "en", False, value)

    @property
    def en1_rx(self):
        """en1_rx: Enable channel 1 RX"""
        return self._get_iio_attr("voltage1", "en", False)

    @en1_rx.setter
    def en1_rx(self, value):
        self._set_iio_attr("voltage1", "en", False, value)

    @property
    def en0_tx(self):
        """en0_tx: Enable channel 0 TX"""
        return self._get_iio_attr("voltage0", "en", True)

    @en0_tx.setter
    def en0_tx(self, value):
        self._set_iio_attr("voltage0", "en", True, value)

    @property
    def en1_tx(self):
        """en1_tx: Enable channel 1 TX"""
        return self._get_iio_attr("voltage1", "en", True)

    @en1_tx.setter
    def en1_tx(self, value):
        self._set_iio_attr("voltage1", "en", True, value)

    @property
    def calibrate_rx_qec_en(self):
        """calibrate_rx_qec_en: Enable RX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_rx_qec_en")

    @calibrate_rx_qec_en.setter
    def calibrate_rx_qec_en(self, value):
        self._set_iio_dev_attr_str("calibrate_rx_qec_en", value)

    @property
    def calibrate_tx_qec_en(self):
        """calibrate_tx_qec_en: Enable TX QEC Calibration"""
        return self._get_iio_dev_attr("calibrate_tx_qec_en")

    @calibrate_tx_qec_en.setter
    def calibrate_tx_qec_en(self, value):
        self._set_iio_dev_attr_str("calibrate_tx_qec_en", value)

    @property
    def calibrate(self):
        """calibrate: Trigger Calibration"""
        return self._get_iio_dev_attr("calibrate")

    @calibrate.setter
    def calibrate(self, value):
        self._set_iio_dev_attr_str("calibrate", value)

    @property
    def gain_control_mode_chan0(self):
        """gain_control_mode_chan0: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str("voltage0", "gain_control_mode", False)

    @gain_control_mode_chan0.setter
    def gain_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def gain_control_mode_chan1(self):
        """gain_control_mode_chan1: Mode of receive path AGC. Options are:
        slow_attack, manual"""
        return self._get_iio_attr_str("voltage1", "gain_control_mode", False)

    @gain_control_mode_chan1.setter
    def gain_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value)

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
        if self.gain_control_mode_chan0 == "manual":
            self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def rx_hardwaregain_chan1(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False)

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        if self.gain_control_mode_chan1 == "manual":
            self._set_iio_attr("voltage1", "hardwaregain", False, value)

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
    def rx_sample_rate(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False)

    @property
    def tx_sample_rate(self):
        """tx_sample_rate: Sample rate TX path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True)

    @property
    def lo1(self):
        """lo1: Carrier frequency of LO1"""
        return self._get_iio_attr("LO1", "frequency", True)

    @lo1.setter
    def lo1(self, value):
        self._set_iio_attr("LO1", "frequency", True, value)

    @property
    def lo2(self):
        """lo2: Carrier frequency of LO2"""
        return self._get_iio_attr("LO2", "frequency", True)

    @lo2.setter
    def lo2(self, value):
        self._set_iio_attr("LO2", "frequency", True, value)

    @property
    def jesd204_fsm_ctrl(self):
        """jesd204_fsm_ctrl: jesd204-fsm control"""
        return self._get_iio_dev_attr("jesd204_fsm_ctrl")

    @jesd204_fsm_ctrl.setter
    def jesd204_fsm_ctrl(self, value):
        self._set_iio_dev_attr_str("jesd204_fsm_ctrl", value)

    @property
    def jesd204_fsm_resume(self):
        """jesd204_fsm_resume: jesd204-fsm resume"""
        return self._get_iio_dev_attr("jesd204_fsm_resume")

    @jesd204_fsm_resume.setter
    def jesd204_fsm_resume(self, value):
        self._set_iio_dev_attr_str("jesd204_fsm_resume", value)

    @property
    def jesd204_fsm_state(self):
        """jesd204_fsm_state: jesd204-fsm state"""
        return self._get_iio_dev_attr_str("jesd204_fsm_state")

    @property
    def jesd204_fsm_paused(self):
        """jesd204_fsm_paused: jesd204-fsm paused"""
        return self._get_iio_dev_attr("jesd204_fsm_paused")

    @property
    def jesd204_fsm_error(self):
        """jesd204_fsm_error: jesd204-fsm error"""
        return self._get_iio_dev_attr("jesd204_fsm_error")
