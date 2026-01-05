# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


def reset_buffer(func):
    """Wrapper for set calls which require the SPI engine.
    Without disabling the buffer the DMA would block forever
    """

    def wrapper(*args, **kwargs):
        if args[0]._reset_on_spi_writes:
            args[0].rx_destroy_buffer()
        func(*args, **kwargs)

    return wrapper


class cn0540(rx, context_manager):
    """CN0540 CBM DAQ Board"""

    _rx_data_si_type = float
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""
    _fda_mode_options = ["low-power", "full-power"]
    _dac_buffer_gain = 1.22
    _g = 0.3
    _fda_gain = 2.667
    _fda_vocm_mv = 2500
    _reset_on_spi_writes = True

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("ad7768-1")
        self._ctrl = self._ctx.find_device("ad7768-1")
        self._ltc2606 = self._ctx.find_device("ltc2606")
        self._gpio = self._ctx.find_device("one-bit-adc-dac")
        self._ltc2308 = self._ctx.find_device("ltc2308")

        rx.__init__(self)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second.
        Valid options are:
        '256000','128000','64000','32000','16000','8000','4000','2000','1000'
        """
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    @reset_buffer
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def input_voltage(self):
        """input_voltage: Input voltage in mV from ADC before shift voltage applied"""
        adc_chan = self._rxadc
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
        return raw * adc_scale * self._dac_buffer_gain

    @property
    def shift_voltage(self):
        """shift_voltage: Shift voltage in mV from LTC2606 to bias sensor data"""
        dac_chan = self._ltc2606
        dac_scale = float(self._get_iio_attr("voltage0", "scale", True, dac_chan))
        raw = self._get_iio_attr("voltage0", "raw", True, dac_chan)
        return raw * dac_scale * self._dac_buffer_gain

    @shift_voltage.setter
    @reset_buffer
    def shift_voltage(self, value):
        dac_chan = self._ltc2606
        dac_scale = float(self._get_iio_attr("voltage0", "scale", True, dac_chan))
        raw = value / (dac_scale * self._dac_buffer_gain)
        self._set_iio_attr_int("voltage0", "raw", True, int(raw), dac_chan)

    @property
    def sensor_voltage(self):
        """sensor_voltage: Sensor voltage in mV read from ADC after biasing"""
        adc_chan = self._rxadc
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)

        v1_st = self._fda_vocm_mv - raw * adc_scale / self._fda_gain
        vsensor_mv = (((self._g + 1) * self.shift_voltage) - v1_st) / self._g

        raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
        vsensor_mv -= raw * adc_scale
        return vsensor_mv

    @property
    def sw_ff_status(self):
        """sw_ff_status: Fault flag status"""
        return self._get_iio_attr("voltage0", "raw", False, self._gpio)

    @property
    def monitor_powerup(self):
        """monitor_powerup: Shutdown pin is tied to active-low inputs"""
        return self._get_iio_attr("voltage2", "raw", True, self._gpio)

    @monitor_powerup.setter
    def monitor_powerup(self, value):
        self._set_iio_attr_int("voltage2", "raw", True, value, self._gpio)

    @property
    def fda_disable_status(self):
        """fda_disable_status: Amplifier disable status"""
        return self._get_iio_attr("voltage5", "raw", True, self._gpio)

    @fda_disable_status.setter
    @reset_buffer
    def fda_disable_status(self, value):
        self._set_iio_attr_int("voltage5", "raw", True, value, self._gpio)

    @property
    def fda_mode(self):
        """fda_mode: Amplifier mode. Options are low-power or full-power"""
        return self._fda_mode_options[
            int(self._get_iio_attr("voltage6", "raw", True, self._gpio))
        ]

    @fda_mode.setter
    def fda_mode(self, value):
        if value not in ["full-power", "low-power"]:
            raise Exception("fda_mode must be low-power or full-power")
        self._set_iio_attr_int(
            "voltage6", "raw", True, int(value == "full-power"), self._gpio
        )

    @property
    def red_led_enable(self):
        """red_led_enable: Enable red LED on board"""
        return self._get_iio_attr("voltage1", "raw", True, self._gpio)

    @red_led_enable.setter
    def red_led_enable(self, value):
        self._set_iio_attr_int("voltage1", "raw", True, value, self._gpio)

    @property
    def sw_cc(self):
        """sw_cc: Enable SW_CC. This will also illuminate the blue LED."""
        return self._get_iio_attr("voltage0", "raw", True, self._gpio)

    @sw_cc.setter
    def sw_cc(self, value):
        self._set_iio_attr_int("voltage0", "raw", True, value, self._gpio)
