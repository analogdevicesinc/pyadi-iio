# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4159(context_manager, attribute):

    """ ADF4159 is a 13 GHz Fractional-N Frequency Synthesizer """

    _device_name = "adf4159"

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)
        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4159 device not found")

    @property
    def ramp_mode(self):
        """Get/Set the Ramp output mode."""
        return self._get_iio_attr_str("altvoltage0", "ramp_mode", True, self._ctrl)

    @ramp_mode.setter
    def ramp_mode(self, value):
        """Get/Set the Ramp output mode."""

        valid = self._get_iio_attr_str(
            "altvoltage0", "ramp_mode_available", True, self._ctrl
        )
        if value not in valid:

            raise ValueError(
                f'ramp_mode of "{value}" is invalid. Valid options: "{valid}"'
            )

        self._set_iio_attr("altvoltage0", "ramp_mode", True, value, self._ctrl)

    @property
    def enable(self):
        """Get/Set the enable status of the RF output."""
        return bool(
            int(self._get_iio_attr("altvoltage0", "powerdown", True, self._ctrl))
        )

    @enable.setter
    def enable(self, value):
        """Get/Set the enable status of the RF output."""
        self._set_iio_attr("altvoltage0", "powerdown", True, int(value), self._ctrl)

    @property
    def frequency(self):
        """Get/Set the Output Frequency of PLL."""
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @frequency.setter
    def frequency(self, value):
        """Get/Set the Output Frequency of PLL."""
        self._set_iio_attr("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def freq_dev_range(self):
        """Get/Set the PLL frequency deviation range."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_range", True, self._ctrl
        )

    @freq_dev_range.setter
    def freq_dev_range(self, value):
        """Get/Set the PLL frequency deviation range."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_range", True, value, self._ctrl
        )

    @property
    def freq_dev_step(self):
        """Get/Set the PLL frequency deviation step."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_step", True, self._ctrl
        )

    @freq_dev_step.setter
    def freq_dev_step(self, value):
        """Get/Set the PLL frequency deviation step."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_step", True, (1 + value), self._ctrl
        )

    @property
    def freq_dev_time(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_deviation_time", True, self._ctrl
        )

    @freq_dev_time.setter
    def freq_dev_time(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_attr(
            "altvoltage0", "frequency_deviation_time", True, value, self._ctrl
        )

    @property
    def phase_value(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_debug_attr("adi,phase", self._ctrl)

    @phase_value.setter
    def phase_value(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_debug_attr_str("adi,phase", str(value), self._ctrl)

    @property
    def trig_delay_en(self):
        """Get/Set the txdata-trigger-delay-enable."""
        return self._get_iio_debug_attr("adi,txdata-trigger-delay-enable", self._ctrl)

    @trig_delay_en.setter
    def trig_delay_en(self, value):
        """Get/Set the txdata-trigger-delay-enable."""
        self._set_iio_debug_attr_str(
            "adi,txdata-trigger-delay-enable", str(value), self._ctrl
        )

    @property
    def sing_ful_tri(self):
        """Get/Set Single-full-triangle-enable."""
        return self._get_iio_debug_attr("adi,single-full-triangle-enable", self._ctrl)

    @sing_ful_tri.setter
    def sing_ful_tri(self, value):
        """Get/Set Single-full-triangle-enable."""
        self._set_iio_debug_attr_str(
            "adi,single-full-triangle-enable", str(value), self._ctrl
        )

    @property
    def tx_trig_en(self):
        """Get/Set tx data trigger enable."""
        return self._get_iio_debug_attr("adi,txdata-trigger-enable", self._ctrl)

    @tx_trig_en.setter
    def tx_trig_en(self, value):
        """Get/Set tx data trigger enable."""
        self._set_iio_debug_attr_str(
            "adi,txdata-trigger-enable", str(value), self._ctrl
        )

    @property
    def ramp_delay_en(self):
        """Get/Set ramp delay enable."""
        return self._get_iio_debug_attr("adi,ramp-delay-enable", self._ctrl)

    @ramp_delay_en.setter
    def ramp_delay_en(self, value):
        """Get/Set ramp delay enable."""
        self._set_iio_debug_attr_str("adi,ramp-delay-enable", str(value), self._ctrl)

    @property
    def delay_clk(self):
        """Get/Set the clk delay enable."""
        return self._get_iio_debug_attr(
            "adi,delay-clk-sel-pfd-x-clk1-enable", self._ctrl
        )

    @delay_clk.setter
    def delay_clk(self, value):
        """Get/Set the clk delay enable."""
        self._set_iio_debug_attr_str(
            "adi,delay-clk-sel-pfd-x-clk1-enable", str(value), self._ctrl
        )

    @property
    def delay_start_en(self):
        """Get/Set the delay start enable."""
        return self._get_iio_debug_attr("adi,delay-start-enable", self._ctrl)

    @delay_start_en.setter
    def delay_start_en(self, value):
        """Get/Set the delay start enable."""
        self._set_iio_debug_attr_str("adi,delay-start-enable", str(value), self._ctrl)

    @property
    def delay_word(self):
        """Get/Set the delay word."""
        return self._get_iio_debug_attr("adi,delay-start-word", self._ctrl)

    @delay_word.setter
    def delay_word(self, value):
        """Get/Set the delay word."""
        self._set_iio_debug_attr_str("adi,delay-start-word", str(value), self._ctrl)

    @property
    def clk1_mode(self):
        """Get/Set the mode of 1st clk."""
        return self._get_iio_debug_attr("adi,clk-div-mode", self._ctrl)

    @clk1_mode.setter
    def clk1_mode(self, value):
        """Get/Set the mode of 1st clk."""
        self._set_iio_debug_attr_str("adi,clk-div-mode", str(value), self._ctrl)

    @property
    def ramp_en(self):
        """Get/Set the ramp enable."""
        return self._get_iio_debug_attr("adi,ramp-enable", self._ctrl)

    @ramp_en.setter
    def ramp_en(self, value):
        """Get/Set the ramp enable."""
        self._set_iio_debug_attr_str("adi,ramp-enable", str(value), self._ctrl)

    @property
    def clk1_div_value(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_debug_attr("adi,clk1-div", self._ctrl)

    @clk1_div_value.setter
    def clk1_div_value(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_debug_attr_str("adi,clk1-div", str(value), self._ctrl)

    @property
    def clk2_div_value(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_debug_attr("adi,clk2-timer-div", self._ctrl)

    @clk2_div_value.setter
    def clk2_div_value(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_debug_attr_str("adi,clk2-timer-div", str(value), self._ctrl)

    @property
    def muxout_sel(self):
        """Get/Set the PLL frequency deviation time."""
        return self._get_iio_debug_attr("adi,muxout-select", self._ctrl)

    @muxout_sel.setter
    def muxout_sel(self, value):
        """Get/Set the PLL frequency deviation time."""
        self._set_iio_debug_attr_str("adi,muxout-select", str(value), self._ctrl)
