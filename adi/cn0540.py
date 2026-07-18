# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import numpy as np

from adi.device_base import rx_def


def reset_buffer(func):
    """Wrapper for set calls which require the SPI engine.
    Without disabling the buffer the DMA would block forever
    """

    def wrapper(*args, **kwargs):
        if args[0]._reset_on_spi_writes:
            args[0].rx_destroy_buffer()
        func(*args, **kwargs)

    return wrapper


class cn0540(rx_def):
    """CN0540 condition-based monitoring data-acquisition board.

    The interface combines buffered AD7768-1 acquisition with the board's
    LTC2606 bias DAC, LTC2308 monitor ADC, and GPIO controls. Voltage
    properties are reported in millivolts.
    """

    _rx_data_si_type = float
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""
    _control_device_name = "ad7768-1"
    _rx_data_device_name = "ad7768-1"
    _fda_mode_options = ["low-power", "full-power"]
    _dac_buffer_gain = 1.22
    _g = 0.3
    _fda_gain = 2.667
    _fda_vocm_mv = 2500
    _reset_on_spi_writes = True

    def __post_init__(self):
        """Discover the board's auxiliary converter and GPIO devices."""
        self._ltc2606 = self._ctx.find_device("ltc2606")
        self._gpio = self._ctx.find_device("one-bit-adc-dac")
        self._ltc2308 = self._ctx.find_device("ltc2308")

    @property
    def sample_rate(self):
        """Sample rate in samples per second."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    @reset_buffer
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def input_voltage(self):
        """Input voltage in mV before the shift voltage is applied."""
        adc_chan = self._rxadc
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
        return raw * adc_scale * self._dac_buffer_gain

    @property
    def shift_voltage(self):
        """LTC2606 shift voltage in mV used to bias the sensor data."""
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
        """Calculated sensor voltage in mV after bias correction."""
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
        """Fault-flag status."""
        return self._get_iio_attr("voltage0", "raw", False, self._gpio)

    @property
    def monitor_powerup(self):
        """Monitor power state; the shutdown pin uses active-low inputs."""
        return self._get_iio_attr("voltage2", "raw", True, self._gpio)

    @monitor_powerup.setter
    def monitor_powerup(self, value):
        self._set_iio_attr_int("voltage2", "raw", True, value, self._gpio)

    @property
    def fda_disable_status(self):
        """Fully differential amplifier disable status."""
        return self._get_iio_attr("voltage5", "raw", True, self._gpio)

    @fda_disable_status.setter
    @reset_buffer
    def fda_disable_status(self, value):
        self._set_iio_attr_int("voltage5", "raw", True, value, self._gpio)

    @property
    def fda_mode(self):
        """Amplifier mode: ``"low-power"`` or ``"full-power"``."""
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
        """Enable or disable the board's red LED."""
        return self._get_iio_attr("voltage1", "raw", True, self._gpio)

    @red_led_enable.setter
    def red_led_enable(self, value):
        self._set_iio_attr_int("voltage1", "raw", True, value, self._gpio)

    @property
    def sw_cc(self):
        """Enable SW_CC and illuminate the blue LED."""
        return self._get_iio_attr("voltage0", "raw", True, self._gpio)

    @sw_cc.setter
    def sw_cc(self, value):
        self._set_iio_attr_int("voltage0", "raw", True, value, self._gpio)
