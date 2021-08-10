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

    _rx_data_type = np.int32
    _rx_data_si_type = np.float
    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _device_name = ""
    _rx_shift = 8
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

    @reset_buffer
    def calibrate(self):
        """Tune LTC2606 to make AD7768-1 ADC codes zero mean"""
        adc_chan = self._rxadc
        dac_chan = self._ltc2606
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        dac_scale = float(self._get_iio_attr("voltage0", "scale", True, dac_chan))

        for _ in range(20):
            raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
            adc_voltage = raw * adc_scale

            raw = self._get_iio_attr("voltage0", "raw", True, dac_chan)
            dac_voltage = (raw * dac_scale - adc_voltage) / dac_scale

            self._set_iio_attr_float(
                "voltage0", "raw", True, int(dac_voltage), dac_chan
            )
            time.sleep(0.01)

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
