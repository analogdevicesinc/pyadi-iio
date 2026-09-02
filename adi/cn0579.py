# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad7768 import ad7768_4


class cn0579(ad7768_4):

    """ CN0579 - Multichannel IEPE DAQ for CbM """

    def __init__(
        self, uri="ip:analog.local",
    ):

        ad7768_4.__init__(self, uri)

        self._gpio = self._ctx.find_device("cn0579_control")
        self._ad5696 = self._ctx.find_device("ad5696")

    @property
    def shift_voltage0(self):
        """shift_voltage: Shift voltage in mV from AD5696 to bias sensor data"""
        dac_chan = self._ad5696
        raw = self._get_iio_attr("voltage0", "raw", True, dac_chan)
        return raw  # * dac_scale * 1.22

    @shift_voltage0.setter
    def shift_voltage0(self, value):
        dac_chan = self._ad5696
        self._set_iio_attr_int("voltage0", "raw", True, int(value), dac_chan)

    @property
    def shift_voltage1(self):
        """shift_voltage: Shift voltage in mV from AD5696 to bias sensor data"""
        dac_chan = self._ad5696
        raw = self._get_iio_attr("voltage1", "raw", True, dac_chan)
        return raw  # * dac_scale * 1.22

    @shift_voltage1.setter
    def shift_voltage1(self, value):
        dac_chan = self._ad5696
        self._set_iio_attr_int("voltage1", "raw", True, int(value), dac_chan)

    @property
    def shift_voltage2(self):
        """shift_voltage: Shift voltage in mV from AD5696 to bias sensor data"""
        dac_chan = self._ad5696
        raw = self._get_iio_attr("voltage2", "raw", True, dac_chan)
        return raw  # * dac_scale * 1.22

    @shift_voltage2.setter
    def shift_voltage2(self, value):
        dac_chan = self._ad5696
        self._set_iio_attr_int("voltage2", "raw", True, int(value), dac_chan)

    @property
    def shift_voltage3(self):
        """shift_voltage: Shift voltage in mV from AD5696 to bias sensor data"""
        dac_chan = self._ad5696
        raw = self._get_iio_attr("voltage3", "raw", True, dac_chan)
        return raw  # * dac_scale * 1.22

    @shift_voltage3.setter
    def shift_voltage3(self, value):
        dac_chan = self._ad5696
        self._set_iio_attr_int("voltage3", "raw", True, int(value), dac_chan)

    @property
    def CC_CH0(self):
        """Get Channel 0 Current Source Control"""
        return self._get_iio_attr("voltage0", "raw", True, self._gpio)

    @CC_CH0.setter
    def CC_CH0(self, value):
        """Set Channel 0 Current Source Control"""
        self._set_iio_attr_int("voltage0", "raw", True, value, self._gpio)

    @property
    def CC_CH1(self):
        """Get Channel 1 Current Source Control"""
        return self._get_iio_attr("voltage1", "raw", True, self._gpio)

    @CC_CH1.setter
    def CC_CH1(self, value):
        """Set Channel 1 Current Source Control"""
        self._set_iio_attr_int("voltage1", "raw", True, value, self._gpio)

    @property
    def CC_CH2(self):
        """Get Channel 2 Current Source Control"""
        return self._get_iio_attr("voltage2", "raw", True, self._gpio)

    @CC_CH2.setter
    def CC_CH2(self, value):
        """Set Channel 2 Current Source Control"""
        self._set_iio_attr_int("voltage2", "raw", True, value, self._gpio)

    @property
    def CC_CH3(self):
        """Get Channel 3 Current Source Control"""
        return self._get_iio_attr("voltage3", "raw", True, self._gpio)

    @CC_CH3.setter
    def CC_CH3(self, value):
        """Set Channel 3 Current Source Control"""
        self._set_iio_attr_int("voltage3", "raw", True, value, self._gpio)
