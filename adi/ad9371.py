
from adi.rx_tx import rx_tx
from adi.context_manager import context_manager


class ad9371(rx_tx, context_manager):
    """ AD9371 Transceiver """
    complex_data = True
    rx_channel_names = ['voltage0_i', 'voltage0_q', 'voltage1_i', 'voltage1_q']
    tx_channel_names = ['voltage0', 'voltage1', 'voltage2', 'voltage3']
    device_name = ""
    rx_enabled_channels = [0, 1]
    tx_enabled_channels = [0, 1]

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self.device_name)

        self.ctrl = self.ctx.find_device("ad9371-phy")
        self.rxadc = self.ctx.find_device("axi-ad9371-rx-hpc")
        self.rxobs = self.ctx.find_device("axi-ad9371-rx-obs-hpc")
        self.txdac = self.ctx.find_device("axi-ad9371-tx-hpc")

        rx_tx.__init__(
            self,
            self.rx_enabled_channels,
            self.tx_enabled_channels)

    @property
    def gain_control_mode(self):
        """gain_control_mode: Mode of receive path AGC. Options are:
        automatic, hybrid, manual"""
        return self.get_iio_attr("voltage0", "gain_control_mode", False)

    @gain_control_mode.setter
    def gain_control_mode(self, value):
        self.set_iio_attr_str("voltage0", "gain_control_mode", False, value)

    @property
    def rx_hardwaregain(self):
        """rx_hardwaregain: Gain applied to RX path. Only applicable when
        gain_control_mode is set to 'manual'"""
        return self.get_iio_attr("voltage0", "hardwaregain", False)

    @rx_hardwaregain.setter
    def rx_hardwaregain(self, value):
        if self.gain_control_mode == 'manual':
            self.set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def tx_hardwaregain(self):
        """tx_hardwaregain: Attenuation applied to TX path"""
        return self.get_iio_attr("voltage0", "hardwaregain", True)

    @tx_hardwaregain.setter
    def tx_hardwaregain(self, value):
        self.set_iio_attr("voltage0", "hardwaregain", True, value)

    @property
    def rx_rf_bandwidth(self):
        """rx_rf_bandwidth: Bandwidth of front-end analog filter of RX path"""
        return self.get_iio_attr("voltage0", "rf_bandwidth", False)

    @property
    def tx_rf_bandwidth(self):
        """tx_rf_bandwidth: Bandwidth of front-end analog filter of TX path"""
        return self.get_iio_attr("voltage0", "rf_bandwidth", True)

    @property
    def rx_sample_rate(self):
        """rx_sample_rate: Sample rate RX path in samples per second"""
        return self.get_iio_attr("voltage0", "sampling_frequency", False)

    @property
    def tx_sample_rate(self):
        """tx_sample_rate: Sample rate TX path in samples per second"""
        return self.get_iio_attr("voltage0", "sampling_frequency", True)

    @property
    def rx_lo(self):
        """rx_lo: Carrier frequency of RX path"""
        return self.get_iio_attr("altvoltage0", "RX_LO_frequency", True)

    @rx_lo.setter
    def rx_lo(self, value):
        self.set_iio_attr("altvoltage0", "RX_LO_frequency", True, value)

    @property
    def tx_lo(self):
        """tx_lo: Carrier frequency of TX path"""
        return self.get_iio_attr("altvoltage1", "TX_LO_frequency", True)

    @tx_lo.setter
    def tx_lo(self, value):
        self.set_iio_attr("altvoltage1", "TX_LO_frequency", True, value)

    @property
    def sn_lo(self):
        """tx_lo: Carrier frequency of TX path"""
        return self.get_iio_attr("altvoltage2", "RX_SN_LO_frequency", True)

    @sn_lo.setter
    def sn_lo(self, value):
        self.set_iio_attr("altvoltage2", "RX_SN_LO_frequency", True, value)
