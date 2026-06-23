# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad9166(attribute, context_manager):
    """ AD9166 Vector Signal Generator """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""
    _temperatureRef = 32.0
    _temperatureRefCode = 0x8008
    _temperatureM = (_temperatureRef + 190) / (_temperatureRefCode / 1000)

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("ad9166")
        self._txdac = self._ctx.find_device("ad9166")
        self._temp_sensor_name = "temp0"
        self._dac0_name = "altvoltage0"

    @property
    def sample_rate(self):
        """ sample_rate: Sets sampling frequency of the AD916x """
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def sample_rate_available(self):
        return [5000000000, 5898240000, 6000000000]

    @property
    def temperature(self):
        """ temperature: Returns the AD916x Chip Temperature in Celsius """
        temp = 0
        if self.temperature_enable:
            try:
                temp = (
                    self._get_iio_attr(self._temp_sensor_name, "input", False) / 1000.0
                )
            except Exception:
                # Use temporary single point calibration if not calibrated
                self.temperature_cal = 34.0
                temp = (
                    self._get_iio_attr(self._temp_sensor_name, "input", False) / 1000.0
                )
            return temp
        return None

    @property
    def temperature_code(self):
        """ temperature_code: Returns the AD916x Chip Temperature ADC code """
        return self._get_iio_attr(self._temp_sensor_name, "raw", False)

    @property
    def temperature_enable(self):
        """ temperature_enable: AD9166 Chip Temperature Measurement Enable

            Options:
                True: Temperature measurement is enabled
                False: Temperature measurement is disabled
        """
        reg = self._ctrl.reg_read(0x135)
        return ((reg and 0x01)) == 0x01

    @temperature_enable.setter
    def temperature_enable(self, value=True):
        if value:
            self._ctrl.reg_write(0x135, 0xA1)
        else:
            self._ctrl.reg_write(0x135, 0xA0)

    @property
    def temperature_cal(self):
        """ temperature_cal: AD9166 Chip Temperature single point calibration value.
        Enter the ambient temperature in degree Celsius.
        """
        return None

    @temperature_cal.setter
    def temperature_cal(self, value=32.0):
        try:
            val = int(round(value * 1000))
            self._set_iio_attr(self._temp_sensor_name, "single_point_calib", False, val)
        except Exception as ex:
            raise ex

    @property
    def nco_enable(self):
        """ nco_enable: AD9166 NCO Modulation Enable:

            Options:
                True: NCO Modulation is enabled
                False: NCO Modulation is disabled
        """
        tmp_reg = self._ctrl.reg_read(0x111) & 0x40
        return tmp_reg != 0

    @nco_enable.setter
    def nco_enable(self, value=True):
        tmp_reg = self._ctrl.reg_read(0x111) & 0xBF
        if value:
            # DATAPATH_CFG (0x111) Bit6=1
            self._ctrl.reg_write(0x111, tmp_reg | 0x40)

        else:
            # DATAPATH_CFG (0x111) Bit6=0
            self._ctrl.reg_write(0x111, tmp_reg)

    @property
    def FIR85_enable(self):
        """ FIR85_enable: AD9166 FIR85 Filter Enable:

            Options:
                True: FIR85 Filter is enabled
                False: FIR85 Filter is disabled
        """
        tmp_reg = self._ctrl.reg_read(0x111) & 0x01
        return tmp_reg != 0

    @FIR85_enable.setter
    def FIR85_enable(self, value=True):
        tmp_reg = self._ctrl.reg_read(0x111) & 0xFE
        if value:
            # DATAPATH_CFG (0x111) Bit0=1
            self._ctrl.reg_write(0x111, tmp_reg | 0x01)
        else:
            # DATAPATH_CFG (0x111) Bit0=0
            self._ctrl.reg_write(0x111, tmp_reg)

    @property
    def tx_enable(self):
        """ tx_enable: AD9166 TX Enable

            Options:
                True: TX is enabled (Datapath is connected to DAC)
                False: TX is disabled or  (DAC input is zeroed)
        """
        tmp_reg = self._ctrl.reg_read(0x03F) & 0x80
        return tmp_reg != 0

    @tx_enable.setter
    def tx_enable(self, value=True):
        # Supports only SPI Data Post Enable/disable.
        # TODO: Implement other tx enable ways.

        tmp_reg = self._ctrl.reg_read(0x03F) & 0x7F
        if value:
            # TX_ENABLE (0x3F) Bit7=1
            self._ctrl.reg_write(0x03F, tmp_reg | 0x80)
        else:
            # TX_ENABLE (0x3F) Bit7=0
            self._ctrl.reg_write(0x03F, tmp_reg)

    @property
    def frequency(self):
        """ frequency: AD916x channel nco frequency value in hz."""
        return self._get_iio_attr(self._dac0_name, "nco_frequency", True)

    @frequency.setter
    def frequency(self, value):
        return self._set_iio_attr(self._dac0_name, "nco_frequency", True, value)

    @property
    def raw(self):
        """ raw: AD916x channel raw value. Integer range 0-32767. """
        return self._get_iio_attr(self._dac0_name, "raw", True)

    @raw.setter
    def raw(self, value):
        return self._set_iio_attr(self._dac0_name, "raw", True, value)
