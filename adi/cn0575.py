# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi


class cn0575:
    """ CN0575 class, exposing onboard temperature sensor, pushbutton,
    and LED. Also reads the platform CPU's temperature, which under
    most operating conditions should be higher than the onboard sensor.
    """

    def __init__(self, uri=""):

        self.gpios = adi.one_bit_adc_dac(uri)
        self.adt75 = adi.lm75(uri)  # ADI version of LM75
        self.gpios.gpio_ext_led = 0  # turn off LED

    @property
    def button(self):
        """Read button state."""
        return self.gpios.gpio_ext_btn

    @property
    def led(self):
        """Read LED state."""
        return self.gpios.gpio_ext_led

    @led.setter
    def led(self, value):
        """Set LED state"""
        self.gpios.gpio_ext_led = value
