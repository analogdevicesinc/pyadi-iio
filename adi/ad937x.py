# Copyright (C) 2019-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.obs import obs
from adi.rx_tx import rx_tx
from adi.sync_start import sync_start


class ad9371(rx_tx, context_manager, sync_start):
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
        self._ctx.set_timeout(30000)  # Needed for loading profiles

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
        try:
            avail = self._get_iio_attr_str(
                "voltage0_i", "sampling_frequency_available", False, self._rxadc
            )
        except KeyError:
            return False
        else:
            avail = avail.strip().split(" ")
            val = self._get_iio_attr_str(
                "voltage0_i", "sampling_frequency", False, self._rxadc
            )
            return val == avail[1]

    @rx_enable_dec8.setter
    def rx_enable_dec8(self, value):
        try:
            avail = self._get_iio_attr_str(
                "voltage0_i", "sampling_frequency_available", False, self._rxadc
            )
        except KeyError:
            if value:
                print(
                    "x8 decimation filter is not supported. Using default sampling frequency."
                )
        else:
            avail = sorted(avail.strip().split(" "))
            val = int(avail[1] if value else avail[0])
            self._set_iio_attr(
                "voltage0_i", "sampling_frequency", False, val, self._rxadc
            )

    @property
    def tx_enable_int8(self):
        """tx_enable_int8: Enable x8 interpolation filter in TX path"""
        try:
            avail = self._get_iio_attr_str(
                "voltage0", "sampling_frequency_available", True, self._txdac
            )
        except KeyError:
            return False
        else:
            avail = avail.strip().split(" ")
            val = self._get_iio_attr_str(
                "voltage0", "sampling_frequency", True, self._txdac
            )
            return val == avail[1]

    @tx_enable_int8.setter
    def tx_enable_int8(self, value):
        try:
            avail = self._get_iio_attr_str(
                "voltage0", "sampling_frequency_available", True, self._txdac
            )
        except KeyError:
            if value:
                print(
                    "x8 interpolation filter is not supported. Using default sampling frequency."
                )
        else:
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

    @property
    def sn_lo(self):
        """sn_lo: Carrier frequency of Sniffer/ORx path"""
        return self._get_iio_attr("altvoltage2", "frequency", True)

    @sn_lo.setter
    def sn_lo(self, value):
        self._set_iio_attr("altvoltage2", "frequency", True, value)

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

    @property
    def profile(self):
        """Load profile file. Provide path to profile file to attribute"""
        return self._get_iio_dev_attr("profile_config")

    @profile.setter
    def profile(self, value):
        with open(value, "r") as file:
            data = file.read()
        self._set_iio_dev_attr_str("profile_config", data)


class ad9375(ad9371):
    """ AD9375 Transceiver """

    @property
    def tx_clgc_tracking_en_chan0(self):
        """Enable CLGC tracking for channel 0"""
        return self._get_iio_attr("voltage0", "clgc_tracking_en", True)

    @tx_clgc_tracking_en_chan0.setter
    def tx_clgc_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "clgc_tracking_en", True, value)

    @property
    def tx_clgc_tracking_en_chan1(self):
        """Enable CLGC tracking for channel 1"""
        return self._get_iio_attr("voltage1", "clgc_tracking_en", True)

    @tx_clgc_tracking_en_chan1.setter
    def tx_clgc_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "clgc_tracking_en", True, value)

    @property
    def tx_clgc_current_gain_chan0(self):
        if self.tx_clgc_tracking_en_chan0 == 1:
            """tx_clgc_current_gain: Current measured gain in 1/100ths dB scale in channel 0.
            Current GaindB = currentGain/100"""
            return self._get_iio_attr("voltage0", "clgc_current_gain", True)
        return

    @property
    def tx_clgc_current_gain_chan1(self):
        """tx_clgc_current_gain: Current measured gain in 1/100ths dB scale in channel 1.
        Current GaindB = currentGain/100"""
        if self.tx_clgc_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "clgc_current_gain", True)
        return

    @property
    def tx_clgc_desired_gain_chan0(self):
        """tx_clgc_desired_gain: Desired gain from channel 0 output to orx input.
        Desired_gain (dB) = Desired_gain/100"""
        if self.tx_clgc_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "clgc_desired_gain", True) / 100
        return

    @tx_clgc_desired_gain_chan0.setter
    def tx_clgc_desired_gain_chan0(self, value):
        value *= 100
        self._set_iio_attr("voltage0", "clgc_desired_gain", True, value)

    @property
    def tx_clgc_desired_gain_chan1(self):
        """tx_clgc_desired_gain: Desired gain from channel 1 output to orx input.
        Desired_gain (dB) = Desired_gain/100"""
        if self.tx_clgc_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "clgc_desired_gain", True) / 100
        return

    @tx_clgc_desired_gain_chan1.setter
    def tx_clgc_desired_gain_chan1(self, value):
        value *= 100
        self._set_iio_attr("voltage1", "clgc_desired_gain", True, value)

    @property
    def tx_clgc_orx_rms_chan0(self):
        """tx_clgc_orx_rms: RMS orx digital sample power measured in the DPD block on the orx side is returned
        with measurement resolution of 0.01 dB for channel 0. Prms dBFs = orxRMS/100"""
        if self.tx_clgc_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "clgc_orx_rms", True) / 100
        return

    @property
    def tx_clgc_track_count_chan0(self):
        """tx_clgc_track_count: The control reads back the number of times the CLGC has successfully run since
        CLGC initialization calibration for channel 0"""
        if self.tx_clgc_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "clgc_track_count", True)
        return

    @property
    def tx_clgc_track_count_chan1(self):
        """tx_clgc_track_count: The control reads back the number of times the CLGC has successfully run since
        CLGC initialization calibration for channel 1"""
        if self.tx_clgc_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "clgc_track_count", True)
        return

    @property
    def tx_clgc_tx_gain_chan0(self):
        """tx_clgc_tx_gain: It controls the current channel 0 attenuation for a channel in 0.05 dB resolution.
        Tx_Attenuation(dB) = Tx_gain/200"""
        if self.tx_clgc_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "clgc_tx_gain", True) * 0.05
        return

    @property
    def tx_clgc_tx_gain_chan1(self):
        """tx_clgc_tx_gain: It controls the current channel 1 attenuation for a channel in 0.05 dB resolution. Tx_Attenuation(dB) = Tx_gain/200"""
        if self.tx_clgc_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "clgc_tx_gain", True) * 0.05
        return

    @property
    def tx_clgc_tx_rms_chan0(self):
        """tx_clgc_tx_rms: The controls returns the RMS channel 0 digital sample power measured at DPD actuator output
        with measurement resolution of 0.01 dB. Prms dBFs = txRMS/100"""
        if self.tx_clgc_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "clgc_tx_rms", True) / 100
        return

    @property
    def tx_clgc_tx_rms_chan1(self):
        """tx_clgc_tx_rms: The controls returns the RMS channel 1 digital sample power measured at DPD actuator output
        with measurement resolution of 0.01 dB. Prms dBFs = txRMS/100"""
        if self.tx_clgc_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "clgc_tx_rms", True) / 100
        return

    @property
    def tx_dpd_actuator_en_chan0(self):
        """Enable DPD actuator for channel 0"""
        return self._get_iio_attr("voltage0", "dpd_actuator_en", True)

    @tx_dpd_actuator_en_chan0.setter
    def tx_dpd_actuator_en_chan0(self, value):
        self._set_iio_attr("voltage0", "dpd_actuator_en", True, value)

    @property
    def tx_dpd_actuator_en_chan1(self):
        """Enable DPD actuator for channel 1"""
        return self._get_iio_attr("voltage1", "dpd_actuator_en", True)

    @tx_dpd_actuator_en_chan1.setter
    def tx_dpd_actuator_en_chan1(self, value):
        self._set_iio_attr("voltage1", "dpd_actuator_en", True, value)

    @property
    def tx_dpd_tracking_en_chan0(self):
        """Enable DPD tracking for channel 0"""
        return self._get_iio_attr("voltage0", "dpd_tracking_en", True)

    @tx_dpd_tracking_en_chan0.setter
    def tx_dpd_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "dpd_tracking_en", True, value)

    @property
    def tx_dpd_tracking_en_chan1(self):
        """Enable DPD tracking for channel 1"""
        return self._get_iio_attr("voltage1", "dpd_tracking_en", True)

    @tx_dpd_tracking_en_chan1.setter
    def tx_dpd_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "dpd_tracking_en", True, value)

    @property
    def tx_dpd_external_path_delay_chan0(self):
        """tx_dpd_external_path_delay: The control reads back the external path delay
        from channel 0 output to orx input at 1/16 sample resolution of the ORx sample rate"""
        if self.tx_dpd_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "dpd_external_path_delay", True) / 16
        return

    @property
    def tx_dpd_external_path_delay_chan1(self):
        """tx_dpd_external_path_delay: The control reads back the external path delay
        from channel 1 output to orx input at 1/16 sample resolution of the ORx sample rate"""
        if self.tx_dpd_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "dpd_external_path_delay", True) / 16
        return

    @property
    def tx_dpd_model_error_chan0(self):
        """tx_dpd_model_error: The control reads back the percent error of the PA model ×10 to include 1 decimal place for channel 0"""
        if self.tx_dpd_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "dpd_model_error", True) / 10
        return

    @property
    def tx_dpd_model_error_chan1(self):
        """tx_dpd_model_error: The control reads back the percent error of the PA model ×10 to include 1 decimal place for channel 1"""
        if self.tx_dpd_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "dpd_model_error", True) / 10
        return

    def tx_dpd_reset_en_chan0(self, value):
        """Enable DPD reset for channel 0"""
        if value == 1:
            self._set_iio_attr("voltage0", "dpd_reset_en", True, value)

    def tx_dpd_reset_en_chan1(self, value):
        """Enable DPD reset for channel 1"""
        if value == 1:
            self._set_iio_attr("voltage1", "dpd_reset_en", True, value)

    @property
    def tx_dpd_status_chan0(self):
        """tx_dpd_status: It reads back the DPD calibration status from the ARM processor for channel 0"""
        # DPD status lookup
        dpdstat_lookup = {
            0: "No Error",
            1: "Error: ORx disabled",
            2: "Error: Tx disabled",
            3: "Error: DPD initialization not run",
            4: "Error: Path delay not setup",
            5: "Error: ORx signal too low",
            6: "Error: ORx signal saturated",
            7: "Error: Tx signal too low",
            8: "Error: Tx signal saturated",
            9: "Error: Model error high",
            10: "Error: AM AM outliers",
            11: "Error: Invalid Tx profile",
            12: "Error: ORx QEC Disabled",
        }
        if self.tx_dpd_tracking_en_chan0 == 1:
            dpdstat_val = self._get_iio_attr("voltage0", "dpd_status", True)
            if dpdstat_val in dpdstat_lookup.keys():
                return dpdstat_lookup[dpdstat_val]
        return

    @property
    def tx_dpd_status_chan1(self):
        """tx_dpd_status: It reads back the DPD calibration status from the ARM processor for channel 1"""
        # DPD status lookup
        dpdstat_lookup = {
            0: "No Error",
            1: "Error: ORx disabled",
            2: "Error: Tx disabled",
            3: "Error: DPD initialization not run",
            4: "Error: Path delay not setup",
            5: "Error: ORx signal too low",
            6: "Error: ORx signal saturated",
            7: "Error: Tx signal too low",
            8: "Error: Tx signal saturated",
            9: "Error: Model error high",
            10: "Error: AM AM outliers",
            11: "Error: Invalid Tx profile",
            12: "Error: ORx QEC Disabled",
        }
        if self.tx_dpd_tracking_en_chan1 == 1:
            dpdstat_val = self._get_iio_attr("voltage1", "dpd_status", True)
            if dpdstat_val in dpdstat_lookup.keys():
                return dpdstat_lookup[dpdstat_val]
        return

    @property
    def tx_dpd_track_count_chan0(self):
        """tx_dpd_track_count: It reads back the number of times the DPD has successfully run since
        DPD initialization calibration for channel 0"""
        if self.tx_dpd_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "dpd_track_count", True)
        return

    @property
    def tx_dpd_track_count_chan1(self):
        """tx_dpd_track_count: It reads back the number of times the DPD has successfully run since
        DPD initialization calibration for channel 1"""
        if self.tx_dpd_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "dpd_track_count", True)
        return

    @property
    def tx_vswr_tracking_en_chan0(self):
        """Enable VSWR tracking for channel 0"""
        return self._get_iio_attr("voltage0", "vswr_tracking_en", True)

    @tx_vswr_tracking_en_chan0.setter
    def tx_vswr_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "vswr_tracking_en", True, value)

    @property
    def tx_vswr_tracking_en_chan1(self):
        """Enable VSWR tracking for channel 1"""
        return self._get_iio_attr("voltage1", "vswr_tracking_en", True)

    @tx_vswr_tracking_en_chan1.setter
    def tx_vswr_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "vswr_tracking_en", True, value)

    @property
    def tx_vswr_forward_gain_chan0(self):
        """tx_vswr_forward: Forward rms gain measured from channel 0 to orx path. 0.01 dB = 1"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "vswr_forward_gain", True) * 0.01
        return

    @property
    def tx_vswr_forward_gain_chan1(self):
        """tx_vswr_forward: Forward rms gain measured from channel 1 to orx path. 0.01 dB = 1"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "vswr_forward_gain", True) * 0.01
        return

    @property
    def tx_vswr_forward_gain_imag_chan0(self):
        """tx_vswr_forward_gain_imag: Imaginary part of the forward path complex gain for channel 0 (1 = 0.01 linear gain)"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "vswr_forward_gain_imag", True) * 0.01
        return

    @property
    def tx_vswr_forward_gain_imag_chan1(self):
        if self.tx_vswr_tracking_en_chan1 == 1:
            """tx_vswr_forward_gain_imag: Imaginary part of the forward path complex gain for channel 1 (1 = 0.01 linear gain)"""
            return self._get_iio_attr("voltage1", "vswr_forward_gain_imag", True) * 0.01
        return

    @property
    def tx_vswr_forward_gain_real_chan0(self):
        """tx_vswr_forward_gain_real: Real part of the forward path complex gain for channel 0 (1 = 0.01 linear gain)"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "vswr_forward_gain_real", True) * 0.01
        return

    @property
    def tx_vswr_forward_gain_real_chan1(self):
        """tx_vswr_forward_gain_real: Real part of the forward path complex gain for channel 1 (1 = 0.01 linear gain)"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "vswr_forward_gain_real", True) * 0.01
        return

    @property
    def tx_vswr_forward_orx_chan0(self):
        """tx_vswr_forward_orx: RMS Orx digital sample power measured at DPD block for ORx data in the forward measurement mode
        with measurement resolution of 0.01 dB and 21 dB offset for channel 0. Prms dBFS = txRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (self._get_iio_attr("voltage0", "vswr_forward_orx", True) / 100) + 21
        return

    @property
    def tx_vswr_forward_tx_chan0(self):
        """tx_vswr_forward_tx: RMS Tx digital sample power measured at DPD block for ORx data in the forward measurement mode
       with measurement resolution of 0.01 dB and 21 dB offset for channel 0. Prms dBFS = txRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (self._get_iio_attr("voltage0", "vswr_forward_tx", True) / 100) + 21
        return

    @property
    def tx_vswr_forward_tx_chan1(self):
        """tx_vswr_forward_tx: RMS Tx digital sample power measured at DPD block for ORx data in the forward measurement mode
       with measurement resolution of 0.01 dB and 21 dB offset for channel 1. Prms dBFS = txRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return (self._get_iio_attr("voltage1", "vswr_forward_tx", True) / 100) + 21
        return

    @property
    def tx_vswr_reflected_gain_chan0(self):
        """tx_vswr_reflected_gain: Reflected path gain in RMS for channel 0. 1 = 0.01 dB gain"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "vswr_reflected_gain", True) * 0.01
        return

    @property
    def tx_vswr_reflected_gain_chan1(self):
        """tx_vswr_reflected_gain: Reflected path gain in RMS for channel 1. 1 = 0.01 dB gain"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "vswr_reflected_gain", True) * 0.01
        return

    @property
    def tx_vswr_reflected_gain_imag_chan0(self):
        """tx_vswr_reflected_gain_imag: Imaginary part of the reflected path complex gain for channel 0. 1 = 0.01 linear gain"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (
                self._get_iio_attr("voltage0", "vswr_reflected_gain_imag", True) * 0.01
            )
        return

    @property
    def tx_vswr_reflected_gain_imag_chan1(self):
        """tx_vswr_reflected_gain_imag: Imaginary part of the reflected path complex gain for channel 1. 1 = 0.01 linear gain"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return (
                self._get_iio_attr("voltage1", "vswr_reflected_gain_imag", True) * 0.01
            )
        return

    @property
    def tx_vswr_reflected_gain_real_chan0(self):
        """tx_vswr_reflected_gain_real: Real part of the reflected path complex gain for channel 0. 1 = 0.01 linear gain"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (
                self._get_iio_attr("voltage0", "vswr_reflected_gain_real", True) * 0.01
            )
        return

    @property
    def tx_vswr_reflected_gain_real_chan1(self):
        """tx_vswr_reflected_gain_real: Real part of the reflected path complex gain for channel 1. 1 = 0.01 linear gain"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return (
                self._get_iio_attr("voltage1", "vswr_reflected_gain_real", True) * 0.01
            )
        return

    @property
    def tx_vswr_reflected_orx_chan0(self):
        """tx_vswr_reflected_orx: RMS ORx digital sample power measured at DPD block for the ORx data in the reverse measurement mode
       with measurement resolution of 0.01 dB and 21 dB offset for channel 0. Prms dBFS = orxRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (
                self._get_iio_attr("voltage0", "vswr_reflected_orx", True) / 100
            ) + 21
        return

    @property
    def tx_vswr_reflected_tx_chan0(self):
        """tx_vswr_reflected_tx: RMS Tx digital sample power measured at DPD actuator for the reverse measurement
       with measurement resolution of 0.01 dB and 21 dB offset for channel 0. Prms dBFS = txRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return (
                self._get_iio_attr("voltage0", "vswr_reflected_tx", True) / 100
            ) + 21
        return

    @property
    def tx_vswr_reflected_tx_chan1(self):
        """tx_vswr_reflected_tx: RMS Tx digital sample power measured at DPD actuator for the reverse measurement
       with measurement resolution of 0.01 dB and 21 dB offset for channel 1. Prms dBFS = txRms/100 + 21 dB"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return (
                self._get_iio_attr("voltage1", "vswr_reflected_tx", True) / 100
            ) + 21
        return

    @property
    def tx_vswr_track_count_chan0(self):
        """tx_vswr_track_count: The control reads back the number of times the VSWR has successfully run
        since VSWR initialization calibration for channel 0"""
        if self.tx_vswr_tracking_en_chan0 == 1:
            return self._get_iio_attr("voltage0", "vswr_track_count", True)
        return

    @property
    def tx_vswr_track_count_chan1(self):
        """tx_vswr_track_count: The control reads back the number of times the VSWR has successfully run since
        VSWR initialization calibration for channel 1"""
        if self.tx_vswr_tracking_en_chan1 == 1:
            return self._get_iio_attr("voltage1", "vswr_track_count", True)
        return
