# Copyright (C) 2020 Analog Devices, Inc.
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
    self._tx2.tx()


class adrv9002(rx_tx, context_manager):
    """ ADRV9002 Transceiver """

    _complex_data = True
    _rx_channel_names = ["voltage0_i", "voltage0_q"]
    _rx2_channel_names = ["voltage0_i", "voltage0_q", "voltage1_i"]
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
            self._rxadc = self._ctx.find_device("axi-adrv9002-rx1-lpc")
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
            self._txdac = self._ctx.find_device("axi-adrv9002-tx1-lpc")
            self._txdac2 = self._ctx.find_device("axi-adrv9002-tx2-lpc")
            self._tx2 = tx_two(self._ctx, self._txdac2, self._tx2_channel_names)
            setattr(adrv9002, "tx1", tx1)
            setattr(adrv9002, "tx2", tx2)
            remap(self._tx2, "tx_", "tx2_", type(self))

        else:
            self._tx_dma_mode = "combined"
            self._tx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
            self._txdac = self._ctx.find_device("axi-adrv9002-tx-lpc")

        self._ctrl = self._ctx.find_device("adrv9002-phy")

        self._ctx.set_timeout(30000)  # Needed for loading profiles

        rx_tx.__init__(self)

    @property
    def profile(self):
        """Load profile file. Provide path to profile file to attribute"""
        return self._get_iio_dev_attr("profile_config")

    @profile.setter
    def profile(self, value):
        with open(value, "r") as file:
            data = file.read()
        self._set_iio_dev_attr_str("profile_config", data)

    @property
    def rx_dma_mode(self):
        """rx_dma_mode: DMA configuration for RX path. Options are:
            combined: RX1 and RX2 share the same rx method
            split: RX1 and RX2 have separate rx methods rx1 and rx2.
                   Typically used when they are at different rates.
                   In this case the standard rx method has the same
                   effect as the rx1 method.
        """
        return self._rx_dma_mode

    @property
    def tx_dma_mode(self):
        """tx_dma_mode: DMA configuration for TX path. Options are:
                combined: TX1 and TX2 share the same tx method
                split: TX1 and TX2 have separate tx methods tx1 and tx2.
                       Typically used when they are at different rates.
                       In this case the standard tx method has the same
                       effect as the tx1 method.
        """
        return self._tx_dma_mode

    # @property
    # def calibrate_rx_phase_correction_en(self):
    #     """calibrate_rx_phase_correction_en: Enable RX Phase Correction Calibration"""
    #     return self._get_iio_dev_attr("calibrate_rx_phase_correction_en")
    #
    # @calibrate_rx_phase_correction_en.setter
    # def calibrate_rx_phase_correction_en(self, value):
    #     self._set_iio_dev_attr_str("calibrate_rx_phase_correction_en", value)
    #
    # @property
    # def calibrate_rx_qec_en(self):
    #     """calibrate_rx_qec_en: Enable RX QEC Calibration"""
    #     return self._get_iio_dev_attr("calibrate_rx_qec_en")
    #
    # @calibrate_rx_qec_en.setter
    # def calibrate_rx_qec_en(self, value):
    #     self._set_iio_dev_attr_str("calibrate_rx_qec_en", value)
    #
    # @property
    # def calibrate_tx_qec_en(self):
    #     """calibrate_tx_qec_en: Enable TX QEC Calibration"""
    #     return self._get_iio_dev_attr("calibrate_tx_qec_en")
    #
    # @calibrate_tx_qec_en.setter
    # def calibrate_tx_qec_en(self, value):
    #     self._set_iio_dev_attr_str("calibrate_tx_qec_en", value)
    #
    # @property
    # def calibrate(self):
    #     """calibrate: Trigger Calibration"""
    #     return self._get_iio_dev_attr("calibrate")
    #
    # @calibrate.setter
    # def calibrate(self, value):
    #     self._set_iio_dev_attr_str("calibrate", value)

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
        manual_spi, manual_pin, automatic"""
        return self._get_iio_attr_str("voltage0", "gain_control_mode", False)

    @gain_control_mode_chan0.setter
    def gain_control_mode_chan0(self, value):
        self._set_iio_attr("voltage0", "gain_control_mode", False, value)

    @property
    def gain_control_mode_chan1(self):
        """gain_control_mode_chan1: Mode of receive path AGC. Options are:
        manual_spi, manual_pin, automatic"""
        return self._get_iio_attr_str("voltage1", "gain_control_mode", False)

    @gain_control_mode_chan1.setter
    def gain_control_mode_chan1(self, value):
        self._set_iio_attr("voltage1", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain_chan0(self):
        """rx_hardwaregain: Gain applied to RX path channel 0. Only applicable when
        gain_control_mode is set to 'manual_spi'"""
        return self._get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain_chan0.setter
    def rx_hardwaregain_chan0(self, value):
        if self.gain_control_mode_chan0 == "manual_spi":
            self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def rx_hardwaregain_chan1(self):
        """rx_hardwaregain: Gain applied to RX path channel 1. Only applicable when
        gain_control_mode is set to 'manual_spi'"""
        return self._get_iio_attr("voltage1", "hardwaregain", False)

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        if self.gain_control_mode_chan1 == "manual_spi":
            self._set_iio_attr("voltage1", "hardwaregain", False, value)

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
    def interface_gain_chan0(self):
        """interface_gain_chan0: Fixed input gain stage for channel 0.
        Options are: 18dB 12dB 6dB 0dB -6dB -12dB -18dB -24dB -30dB -36dB """
        return self._get_iio_attr_str("voltage0", "interface_gain", False)

    @interface_gain_chan0.setter
    def interface_gain_chan0(self, value):
        self._set_iio_attr("voltage0", "interface_gain", False, value)

    @property
    def interface_gain_chan1(self):
        """interface_gain_chan0: Fixed input gain stage for channel 0.
        Options are: 18dB 12dB 6dB 0dB -6dB -12dB -18dB -24dB -30dB -36dB """
        return self._get_iio_attr_str("voltage1", "interface_gain", False)

    @interface_gain_chan1.setter
    def interface_gain_chan1(self, value):
        self._set_iio_attr("voltage1", "interface_gain", False, value)

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
    def rx1_lo(self):
        """rx1_lo: Carrier frequency of RX1 path"""
        return self._get_iio_attr("altvoltage0", "RX1_LO_frequency", True)

    @rx1_lo.setter
    def rx1_lo(self, value):
        self._set_iio_attr("altvoltage0", "RX1_LO_frequency", True, value)

    @property
    def tx1_lo(self):
        """tx1_lo: Carrier frequency of TX1 path"""
        return self._get_iio_attr("altvoltage2", "TX1_LO_frequency", True)

    @tx1_lo.setter
    def tx1_lo(self, value):
        self._set_iio_attr("altvoltage2", "TX1_LO_frequency", True, value)
