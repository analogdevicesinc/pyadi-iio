# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from ctypes import c_char_p

import iio

from adi.context_manager import context_manager
from adi.obs import obs, remap, tx_two
from adi.rx_tx import rx_tx


def rx1(self):
    """rx1: Receive data on channel 0 (Same as rx() method) """
    return self.rx()


def rx2(self):
    """rx2: Receive data on channel 1 """
    return self._rx2.rx()


def tx1(self, data):
    """tx1: Transmit data on channel 0 (Same as tx() method) """
    self.tx(data)


def tx2(self, data):
    """tx2: Transmit data on channel 1 """
    self._tx2.tx(data)


class adrv9002(rx_tx, context_manager):
    """ ADRV9002 Transceiver """

    _complex_data = True
    _rx_channel_names = ["voltage0_i", "voltage0_q"]
    _rx2_channel_names = ["voltage0_i", "voltage0_q"]
    _tx_channel_names = ["voltage0", "voltage1"]
    _tx2_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Determine if we have a split or combined DMA
        devs = self._ctx.devices
        rxdevs = list(filter(lambda dev: "rx" in str(dev.name), devs))
        txdevs = list(filter(lambda dev: "tx" in str(dev.name), devs))

        if len(rxdevs) > 1:
            self._rx_dma_mode = "split"
            self._rxadc = self._ctx.find_device("axi-adrv9002-rx-lpc")
            self._rxadc2 = self._ctx.find_device("axi-adrv9002-rx2-lpc")
            self._rx2 = obs(self._ctx, self._rxadc2, self._rx2_channel_names)
            setattr(adrv9002, "rx1", rx1)
            setattr(adrv9002, "rx2", rx2)
            remap(self._rx2, "rx_", "rx2_", type(self))

        else:
            self._rx_dma_mode = "combined"
            self._rx_channel_names = [
                "voltage0_i",
                "voltage0_q",
                "voltage1_i",
                "voltage1_q",
            ]
            self._rxadc = self._ctx.find_device("axi-adrv9002-rx-lpc")

        if len(txdevs) > 1:
            self._tx_dma_mode = "split"
            self._txdac = self._ctx.find_device("axi-adrv9002-tx-lpc")
            self._txdac2 = self._ctx.find_device("axi-adrv9002-tx2-lpc")
            self._tx2 = tx_two(self._ctx, self._txdac2, self._tx2_channel_names)
            setattr(adrv9002, "tx1", tx1)
            setattr(adrv9002, "tx2", tx2)
            remap(self._tx2, "tx_", "tx2_", type(self))
            remap(self._tx2, "dds_", "dds2_", type(self))

        else:
            self._tx_dma_mode = "combined"
            self._tx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
            self._txdac = self._ctx.find_device("axi-adrv9002-tx-lpc")

        self._ctrl = self._ctx.find_device("adrv9002-phy")

        self._ctx.set_timeout(30000)  # Needed for loading profiles

        rx_tx.__init__(self)

    def write_stream_profile(self, stream, profile):
        """Load a new profile and stream on the device"""
        with open(stream, "rb") as file:
            data = file.read()
            data = c_char_p(data)
            attr_encode = "stream_config".encode("ascii")
            iio._d_write_attr(self._ctrl._device, attr_encode, data)
        with open(profile, "r") as file:
            data = file.read()
        self._set_iio_dev_attr_str("profile_config", data)

    def write_profile(self, value):
        """Load a new profile on the device
            Stream related to profile should be loaded first.
            Please see driver documentation about profile generation.
        """
        with open(value, "r") as file:
            data = file.read()
        self._set_iio_dev_attr_str("profile_config", data)

    def write_stream(self, value):
        """Load a new stream on the device
            Stream becomes active once accompanying profile is loaded
            Please see driver documentation about stream generation.
        """
        with open(value, "rb") as file:
            data = file.read()
            data = c_char_p(data)
            attr_encode = "stream_config".encode("ascii")
            iio._d_write_attr(self._ctrl._device, attr_encode, data)

    @property
    def profile(self):
        profile_data = self._get_iio_dev_attr_str("profile_config")
        return dict(x.split(": ") for x in profile_data.split("\n"))

    # we cannot really get the stream. The driver will just throw EPERM
    stream = property(None, write_stream)

    @property
    def rx_dma_mode(self):
        """rx_dma_mode: DMA configuration for RX path. Options are:
            combined: RX1 and RX2 share the same rx method
            split: RX1 and RX2 have separate rx methods rx1 and rx2. Typically
            used when they are at different rates. In this case the standard rx
            method has the same effect as the rx1 method.
        """
        return self._rx_dma_mode

    @property
    def tx_dma_mode(self):
        """tx_dma_mode: DMA configuration for TX path. Options are:
                combined: TX1 and TX2 share the same tx method
                split: TX1 and TX2 have separate tx methods tx1 and tx2.
                Typically used when they are at different rates. In this case
                the standard tx method has the same effect as the tx1 method.
        """
        return self._tx_dma_mode

    @property
    def rx_ensm_mode_chan0(self):
        """rx_ensm_mode_chan0: RX Enable State Machine State Channel 0. Options are:
        calibrated, primed, rf_enabled"""
        return self._get_iio_attr_str("voltage0", "ensm_mode", False)

    @rx_ensm_mode_chan0.setter
    def rx_ensm_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "ensm_mode", False, value)

    @property
    def rx_ensm_mode_chan1(self):
        """rx_ensm_mode_chan1: RX Enable State Machine State Channel 1. Options are:
        calibrated, primed, rf_enabled"""
        return self._get_iio_attr_str("voltage1", "ensm_mode", False)

    @rx_ensm_mode_chan1.setter
    def rx_ensm_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "ensm_mode", False, value)

    @property
    def tx_ensm_mode_chan0(self):
        """tx_ensm_mode_chan0: TX Enable State Machine State Channel 0. Options are:
        calibrated, primed, rf_enabled"""
        return self._get_iio_attr_str("voltage0", "ensm_mode", True)

    @tx_ensm_mode_chan0.setter
    def tx_ensm_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "ensm_mode", True, value)

    @property
    def tx_ensm_mode_chan1(self):
        """tx_ensm_mode_chan1: TX Enable State Machine State Channel 1. Options are:
        calibrated, primed, rf_enabled"""
        return self._get_iio_attr_str("voltage1", "ensm_mode", True)

    @tx_ensm_mode_chan1.setter
    def tx_ensm_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "ensm_mode", True, value)

    @property
    def gain_control_mode_chan0(self):
        """gain_control_mode_chan0: Mode of receive path AGC. Options are:
        spi, pin, automatic"""
        return self._get_iio_attr_str("voltage0", "gain_control_mode", False)

    @gain_control_mode_chan0.setter
    def gain_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def gain_control_mode_chan1(self):
        """gain_control_mode_chan1: Mode of receive path AGC. Options are:
        spi, pin, automatic"""
        return self._get_iio_attr_str("voltage1", "gain_control_mode", False)

    @gain_control_mode_chan1.setter
    def gain_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain_chan0(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'spi'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain_chan0.setter
    def rx_hardwaregain_chan0(self, value):
        if self.gain_control_mode_chan0 == "spi":
            self._set_iio_attr("voltage0", "hardwaregain", False, value)
        else:
            raise RuntimeError("gain_control_mode_chan0 must be set to spi")

    @property
    def rx_hardwaregain_chan1(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'spi'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False)

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        if self.gain_control_mode_chan1 == "spi":
            self._set_iio_attr("voltage1", "hardwaregain", False, value)
        else:
            raise RuntimeError("gain_control_mode_chan1 must be set to spi")

    @property
    def tx_hardwaregain_chan0(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 0"""
        return self._get_iio_attr("voltage0", "hardwaregain", True)

    @tx_hardwaregain_chan0.setter
    def tx_hardwaregain_chan0(self, value):
        if self.atten_control_mode_chan0 == "spi":
            self._set_iio_attr("voltage0", "hardwaregain", True, value)
        else:
            raise RuntimeError("atten_control_mode_chan0 must be set to spi")

    @property
    def tx_hardwaregain_chan1(self):
        """tx_hardwaregain: Attenuation applied to TX path channel 1"""
        return self._get_iio_attr("voltage1", "hardwaregain", True)

    @tx_hardwaregain_chan1.setter
    def tx_hardwaregain_chan1(self, value):
        if self.atten_control_mode_chan1 == "spi":
            self._set_iio_attr("voltage1", "hardwaregain", True, value)
        else:
            raise RuntimeError("atten_control_mode_chan1 must be set to spi")

    @property
    def interface_gain_chan0(self):
        """interface_gain_chan0: Fixed input gain stage for channel 0.
        Options are: 18dB 12dB 6dB 0dB -6dB -12dB -18dB -24dB -30dB -36dB """
        return self._get_iio_attr_str("voltage0", "interface_gain", False)

    @interface_gain_chan0.setter
    def interface_gain_chan0(self, value):
        if (
            self.digital_gain_control_mode_chan0 == "spi"
        ) and self.rx_ensm_mode_chan0 == "rf_enabled":
            self._set_iio_attr("voltage0", "interface_gain", False, value)

    @property
    def interface_gain_chan1(self):
        """interface_gain_chan0: Fixed input gain stage for channel 0.
        Options are: 18dB 12dB 6dB 0dB -6dB -12dB -18dB -24dB -30dB -36dB """
        return self._get_iio_attr_str("voltage1", "interface_gain", False)

    @interface_gain_chan1.setter
    def interface_gain_chan1(self, value):
        if (
            self.digital_gain_control_mode_chan1 == "spi"
        ) and self.rx_ensm_mode_chan1 == "rf_enabled":
            self._set_iio_attr("voltage1", "interface_gain", False, value)

    @property
    def agc_tracking_en_chan0(self):
        """Enable AGC on the fly tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "agc_tracking_en", False)

    @agc_tracking_en_chan0.setter
    def agc_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "agc_tracking_en", False, value)

    @property
    def bbdc_rejection_tracking_en_chan0(self):
        """"Enable Baseband DC rejection on the fly tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "bbdc_rejection_tracking_en", False)

    @bbdc_rejection_tracking_en_chan0.setter
    def bbdc_rejection_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "bbdc_rejection_tracking_en", False, value)

    @property
    def hd_tracking_en_chan0(self):
        """"Enable Harmonic Distortion on the fly tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "hd_tracking_en", False)

    @hd_tracking_en_chan0.setter
    def hd_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "hd_tracking_en", False, value)

    @property
    def quadrature_fic_tracking_en_chan0(self):
        """Enable Quadrature Error Correction Narrowband FIC on the fly tracking
        calibration for RX1"""
        return self._get_iio_attr("voltage0", "quadrature_fic_tracking_en", False)

    @quadrature_fic_tracking_en_chan0.setter
    def quadrature_fic_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "quadrature_fic_tracking_en", False, value)

    @property
    def quadrature_w_poly_tracking_en_chan0(self):
        """Enable Quadrature Error Correction Wideband Poly on the fly tracking
        calibration for RX1"""
        return self._get_iio_attr("voltage0", "quadrature_w_poly_tracking_en", False)

    @quadrature_w_poly_tracking_en_chan0.setter
    def quadrature_w_poly_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "quadrature_w_poly_tracking_en", False, value)

    @property
    def rfdc_tracking_en_chan0(self):
        """"Enable RF DC on the fly tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "rfdc_tracking_en", False)

    @rfdc_tracking_en_chan0.setter
    def rfdc_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "rfdc_tracking_en", False, value)

    @property
    def rssi_tracking_en_chan0(self):
        """"Enable RSSI on the fly tracking calibration for RX1"""
        return self._get_iio_attr("voltage0", "rssi_tracking_en", False)

    @rssi_tracking_en_chan0.setter
    def rssi_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "rssi_tracking_en", False, value)

    @property
    def agc_tracking_en_chan1(self):
        """Enable AGC on the fly tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "agc_tracking_en", False)

    @agc_tracking_en_chan1.setter
    def agc_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "agc_tracking_en", False, value)

    @property
    def bbdc_rejection_tracking_en_chan1(self):
        """"Enable Baseband DC rejection on the fly tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "bbdc_rejection_tracking_en", False)

    @bbdc_rejection_tracking_en_chan1.setter
    def bbdc_rejection_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "bbdc_rejection_tracking_en", False, value)

    @property
    def hd_tracking_en_chan1(self):
        """"Enable Harmonic Distortion on the fly tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "hd_tracking_en", False)

    @hd_tracking_en_chan1.setter
    def hd_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "hd_tracking_en", False, value)

    @property
    def quadrature_fic_tracking_en_chan1(self):
        """Enable Quadrature Error Correction Narrowband FIC on the fly tracking
        calibration for RX2"""
        return self._get_iio_attr("voltage1", "quadrature_fic_tracking_en", False)

    @quadrature_fic_tracking_en_chan1.setter
    def quadrature_fic_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "quadrature_fic_tracking_en", False, value)

    @property
    def quadrature_w_poly_tracking_en_chan1(self):
        """Enable Quadrature Error Correction Wideband Poly on the fly tracking
        calibration for RX2"""
        return self._get_iio_attr("voltage1", "quadrature_w_poly_tracking_en", False)

    @quadrature_w_poly_tracking_en_chan1.setter
    def quadrature_w_poly_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "quadrature_w_poly_tracking_en", False, value)

    @property
    def rfdc_tracking_en_chan1(self):
        """"Enable RF DC on the fly tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "rfdc_tracking_en", False)

    @rfdc_tracking_en_chan1.setter
    def rfdc_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "rfdc_tracking_en", False, value)

    @property
    def rssi_tracking_en_chan1(self):
        """"Enable RSSI on the fly tracking calibration for RX2"""
        return self._get_iio_attr("voltage1", "rssi_tracking_en", False)

    @rssi_tracking_en_chan1.setter
    def rssi_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "rssi_tracking_en", False, value)

    @property
    def close_loop_gain_tracking_en_chan0(self):
        """Enable Close Loop Gain tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "close_loop_gain_tracking_en", True)

    @close_loop_gain_tracking_en_chan0.setter
    def close_loop_gain_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "close_loop_gain_tracking_en", True, value)

    @property
    def lo_leakage_tracking_en_chan0(self):
        """Enable LO Leakage tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "lo_leakage_tracking_en", True)

    @lo_leakage_tracking_en_chan0.setter
    def lo_leakage_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "lo_leakage_tracking_en", True, value)

    @property
    def loopback_delay_tracking_en_chan0(self):
        """Enable Loopback delay tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "loopback_delay_tracking_en", True)

    @loopback_delay_tracking_en_chan0.setter
    def loopback_delay_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "loopback_delay_tracking_en", True, value)

    @property
    def pa_correction_tracking_en_chan0(self):
        """Enable PA Correction tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "pa_correction_tracking_en", True)

    @pa_correction_tracking_en_chan0.setter
    def pa_correction_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "pa_correction_tracking_en", True, value)

    @property
    def quadrature_tracking_en_chan0(self):
        """Enable Quadrature tracking calibration for TX1"""
        return self._get_iio_attr("voltage0", "quadrature_tracking_en", True)

    @quadrature_tracking_en_chan0.setter
    def quadrature_tracking_en_chan0(self, value):
        self._set_iio_attr("voltage0", "quadrature_tracking_en", True, value)

    @property
    def close_loop_gain_tracking_en_chan1(self):
        """Enable Close Loop Gain tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "close_loop_gain_tracking_en", True)

    @close_loop_gain_tracking_en_chan1.setter
    def close_loop_gain_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "close_loop_gain_tracking_en", True, value)

    @property
    def lo_leakage_tracking_en_chan1(self):
        """Enable LO Leakage tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "lo_leakage_tracking_en", True)

    @lo_leakage_tracking_en_chan1.setter
    def lo_leakage_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "lo_leakage_tracking_en", True, value)

    @property
    def loopback_delay_tracking_en_chan1(self):
        """Enable Loopback delay tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "loopback_delay_tracking_en", True)

    @loopback_delay_tracking_en_chan1.setter
    def loopback_delay_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "loopback_delay_tracking_en", True, value)

    @property
    def pa_correction_tracking_en_chan1(self):
        """Enable PA Correction tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "pa_correction_tracking_en", True)

    @pa_correction_tracking_en_chan1.setter
    def pa_correction_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "pa_correction_tracking_en", True, value)

    @property
    def quadrature_tracking_en_chan1(self):
        """Enable Quadrature tracking calibration for TX2"""
        return self._get_iio_attr("voltage1", "quadrature_tracking_en", True)

    @quadrature_tracking_en_chan1.setter
    def quadrature_tracking_en_chan1(self, value):
        self._set_iio_attr("voltage1", "quadrature_tracking_en", True, value)

    @property
    def digital_gain_control_mode_chan0(self):
        """Digital gain control mode for RX1. Option are: automatic spi."""
        return self._get_iio_attr_str("voltage0", "digital_gain_control_mode", False)

    @digital_gain_control_mode_chan0.setter
    def digital_gain_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "digital_gain_control_mode", False, value)

    @property
    def digital_gain_control_mode_chan1(self):
        """ Digital gain control mode for RX2. Option are: automatic spi."""
        return self._get_iio_attr_str("voltage1", "digital_gain_control_mode", False)

    @digital_gain_control_mode_chan1.setter
    def digital_gain_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "digital_gain_control_mode", False, value)

    @property
    def rx0_port_en(self):
        """Control Port RF Enable mode for RX1. Options are: pin and spi"""
        return self._get_iio_attr_str("voltage0", "port_en_mode", False)

    @rx0_port_en.setter
    def rx0_port_en(self, value):
        self._set_iio_attr("voltage0", "port_en_mode", False, value)

    @property
    def tx0_port_en(self):
        """Control Port RF Enable mode for TX1. Options are: pin and spi"""
        return self._get_iio_attr_str("voltage0", "port_en_mode", True)

    @tx0_port_en.setter
    def tx0_port_en(self, value):
        self._set_iio_attr("voltage0", "port_en_mode", True, value)

    @property
    def rx1_port_en(self):
        """Control Port RF Enable mode for RX2. Options are: pin and spi"""
        return self._get_iio_attr_str("voltage1", "port_en_mode", False)

    @rx1_port_en.setter
    def rx1_port_en(self, value):
        self._set_iio_attr("voltage1", "port_en_mode", False, value)

    @property
    def tx1_port_en(self):
        """Control Port RF Enable mode for TX2. Options are: pin and spi"""
        return self._get_iio_attr_str("voltage1", "port_en_mode", True)

    @tx1_port_en.setter
    def tx1_port_en(self, value):
        self._set_iio_attr("voltage1", "port_en_mode", True, value)

    @property
    def rx0_en(self):
        """Control RX1 Power state"""
        return self._get_iio_attr("voltage0", "en", False)

    @rx0_en.setter
    def rx0_en(self, value):
        self._set_iio_attr("voltage0", "en", False, value)

    @property
    def tx0_en(self):
        """"Control TX1 Power state"""
        return self._get_iio_attr("voltage0", "en", True)

    @tx0_en.setter
    def tx0_en(self, value):
        self._set_iio_attr("voltage0", "en", True, value)

    @property
    def rx1_en(self):
        """"Control RX2 Power state"""
        return self._get_iio_attr("voltage1", "en", False)

    @rx1_en.setter
    def rx1_en(self, value):
        self._set_iio_attr("voltage1", "en", False, value)

    @property
    def tx1_en(self):
        """"Control TX2 Power state"""
        return self._get_iio_attr("voltage1", "en", True)

    @tx1_en.setter
    def tx1_en(self, value):
        self._set_iio_attr("voltage1", "en", True, value)

    @property
    def rx0_nco_frequency(self):
        """NCO correction frequency for RX1"""
        return self._get_iio_attr("voltage0", "nco_frequency", False)

    @rx0_nco_frequency.setter
    def rx0_nco_frequency(self, value):
        self._set_iio_attr("voltage0", "nco_frequency", False, value)

    @property
    def tx0_nco_frequency(self):
        """NCO correction frequency for TX1"""
        return self._get_iio_attr("voltage0", "nco_frequency", True)

    @tx0_nco_frequency.setter
    def tx0_nco_frequency(self, value):
        self._set_iio_attr("voltage0", "nco_frequency", True, value)

    @property
    def rx1_nco_frequency(self):
        """NCO correction frequency for RX2"""
        return self._get_iio_attr("voltage1", "nco_frequency", False)

    @rx1_nco_frequency.setter
    def rx1_nco_frequency(self, value):
        self._set_iio_attr("voltage1", "nco_frequency", False, value)

    @property
    def tx1_nco_frequency(self):
        """NCO correction frequency for TX2"""
        return self._get_iio_attr("voltage1", "nco_frequency", True)

    @tx1_nco_frequency.setter
    def tx1_nco_frequency(self, value):
        self._set_iio_attr("voltage1", "nco_frequency", True, value)

    @property
    def atten_control_mode_chan0(self):
        """Control TX1 attenuation mode. Options are: bypass, spi, pin"""
        return self._get_iio_attr_str("voltage0", "atten_control_mode", True)

    @atten_control_mode_chan0.setter
    def atten_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "atten_control_mode", True, value)

    @property
    def atten_control_mode_chan1(self):
        """Control TX2 attenuation mode. Options are: bypass, spi, pin"""
        return self._get_iio_attr_str("voltage1", "atten_control_mode", True)

    @atten_control_mode_chan1.setter
    def atten_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "atten_control_mode", True, value)

    @property
    def rx0_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX1 path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", False)

    @property
    def tx0_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX1 path"""
        return self._get_iio_attr("voltage0", "rf_bandwidth", True)

    @property
    def rx0_sample_rate(self):
        """rx_sample_rate: Sample rate RX1 path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", False)

    @property
    def tx0_sample_rate(self):
        """tx_sample_rate: Sample rate TX1 path in samples per second"""
        return self._get_iio_attr("voltage0", "sampling_frequency", True)

    @property
    def rx1_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX2 path"""
        return self._get_iio_attr("voltage1", "rf_bandwidth", False)

    @property
    def tx1_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX2 path"""
        return self._get_iio_attr("voltage1", "rf_bandwidth", True)

    @property
    def rx1_sample_rate(self):
        """rx_sample_rate: Sample rate RX2 path in samples per second"""
        return self._get_iio_attr("voltage1", "sampling_frequency", False)

    @property
    def tx1_sample_rate(self):
        """tx_sample_rate: Sample rate TX2 path in samples per second"""
        return self._get_iio_attr("voltage1", "sampling_frequency", True)

    @property
    def rx0_lo(self):
        """rx0_lo: Carrier frequency of RX1 path"""
        return self._get_iio_attr("altvoltage0", "frequency", True)

    @rx0_lo.setter
    def rx0_lo(self, value):
        self._set_iio_attr("altvoltage0", "frequency", True, value)

    @property
    def rx1_lo(self):
        """rx1_lo: Carrier frequency of RX2 path"""
        return self._get_iio_attr("altvoltage1", "frequency", True)

    @rx1_lo.setter
    def rx1_lo(self, value):
        self._set_iio_attr("altvoltage1", "frequency", True, value)

    @property
    def tx0_lo(self):
        """tx1_lo: Carrier frequency of TX1 path"""
        return self._get_iio_attr("altvoltage2", "frequency", True)

    @tx0_lo.setter
    def tx0_lo(self, value):
        self._set_iio_attr("altvoltage2", "frequency", True, value)

    @property
    def tx1_lo(self):
        """tx1_lo: Carrier frequency of TX2 path"""
        return self._get_iio_attr("altvoltage3", "frequency", True)

    @tx1_lo.setter
    def tx1_lo(self, value):
        self._set_iio_attr("altvoltage3", "frequency", True, value)

    @property
    def api_version(self):
        """api_version: Get the version of the API"""
        return self._get_iio_debug_attr_str("api_version")
