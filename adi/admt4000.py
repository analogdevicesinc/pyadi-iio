# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class admt4000(rx, context_manager, attribute):
    """ADMT4000 True power-on multiturn sensor"""

    _rx_data_type = np.int16
    _rx_unbuffered_data = False
    _rx_data_si_type = float

    disable_trigger = False
    def __init__(self, uri="", device_name=None, trigger_name=None):
        """admt4000 class constructor."""
        context_manager.__init__(self, uri)

        compatible_parts = [
            "admt4000",
        ]

        self.admt4000_ctrl = None

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                print("Found device {}".format(device.name))
                self.admt4000_ctrl = device
                self._ctrl = device
                self._rxadc = device
                self._device_name = device.name
                if not trigger_name:
                    trigger_name = device.name + "-dev0"
                break

        if self.admt4000_ctrl is None:
            raise Exception("No compatible device found")

        self.turns = self._channel(self.admt4000_ctrl, "turns")
        self.angle = self._channel(self.admt4000_ctrl, "angle")
        self.temp = self._channel(self.admt4000_ctrl, "temp")
        self._rx_channel_names = ["turns", "angle", "temp"]
        if not self.disable_trigger:
            self._trigger = self._ctx.find_device(trigger_name)
            self._rxadc._set_trigger(self._trigger)
    
        rx.__init__(self)
        self.rx_buffer_size = 20  # Make default buffer smaller

    @property
    def sequencer_mode(self):
        """ADMT4000 sequencer mode."""
        return self._get_iio_dev_attr_str("sequencer_mode", self.admt4000_ctrl)

    @sequencer_mode.setter
    def sequencer_mode(self, value):
        self._set_iio_dev_attr_str("sequencer_mode", value, self.admt4000_ctrl)

    @property
    def angle_filter_en(self):
        """ADMT4000 angle filter."""
        return self._get_iio_dev_attr_str("angle_filter_enable", self.admt4000_ctrl)

    @angle_filter_en.setter
    def angle_filter_en(self, value):
        self._set_iio_dev_attr_str("angle_filter_enable", value, self.admt4000_ctrl)

    @property
    def conversion_mode(self):
        """ADMT4000 conversion mode."""
        return self._get_iio_dev_attr_str("conversion_mode", self.admt4000_ctrl)

    @conversion_mode.setter
    def conversion_mode(self, value):
        self._set_iio_dev_attr_str("conversion_mode", value, self.admt4000_ctrl)

    @property
    def h8_corr_source(self):
        """ADMT4000 Select 8th harmonic correction source."""
        return self._get_iio_dev_attr_str("h8_corr_src", self.admt4000_ctrl)

    @h8_corr_source.setter
    def h8_corr_source(self, value):
        self._set_iio_dev_attr_str("h8_corr_src", value, self.admt4000_ctrl)

    @property
    def h1_mag_corr(self):
        """ADMT4000 1st harmonic correction coefficient magnitude."""
        return self._get_iio_dev_attr_str("h1_mag_corr", self.admt4000_ctrl)

    @h1_mag_corr.setter
    def h1_mag_corr(self, value):
        self._set_iio_dev_attr_str("h1_mag_corr", value, self.admt4000_ctrl)

    @property
    def h1_phase_corr(self):
        """ADMT4000 1st harmonic correction coefficient phase."""
        return self._get_iio_dev_attr_str("h1_ph_corr", self.admt4000_ctrl)

    @h1_phase_corr.setter
    def h1_phase_corr(self, value):
        self._set_iio_dev_attr_str("h1_ph_corr", value, self.admt4000_ctrl)

    @property
    def h2_mag_corr(self):
        """ADMT4000 2nd harmonic correction coefficient magnitude."""
        return self._get_iio_dev_attr_str("h2_mag_corr", self.admt4000_ctrl)

    @h2_mag_corr.setter
    def h2_mag_corr(self, value):
        self._set_iio_dev_attr_str("h2_mag_corr", value, self.admt4000_ctrl)

    @property
    def h2_phase_corr(self):
        """ADMT4000 2nd harmonic correction coefficient phase."""
        return self._get_iio_dev_attr_str("h2_ph_corr", self.admt4000_ctrl)

    @h2_phase_corr.setter
    def h2_phase_corr(self, value):
        self._set_iio_dev_attr_str("h2_ph_corr", value, self.admt4000_ctrl)

    @property
    def h3_mag_corr(self):
        """ADMT4000 3rd harmonic correction coefficient magnitude."""
        return self._get_iio_dev_attr_str("h3_mag_corr", self.admt4000_ctrl)

    @h3_mag_corr.setter
    def h3_mag_corr(self, value):
        self._set_iio_dev_attr_str("h3_mag_corr", value, self.admt4000_ctrl)

    @property
    def h3_phase_corr(self):
        """ADMT4000 3rd harmonic correction coefficient phase."""
        return self._get_iio_dev_attr_str("h3_ph_corr", self.admt4000_ctrl)

    @h3_phase_corr.setter
    def h3_phase_corr(self, value):
        self._set_iio_dev_attr_str("h3_ph_corr", value, self.admt4000_ctrl)

    @property
    def h8_mag_corr(self):
        """ADMT4000 8th harmonic correction coefficient magnitude."""
        return self._get_iio_dev_attr_str("h8_mag_corr", self.admt4000_ctrl)

    @h8_mag_corr.setter
    def h8_mag_corr(self, value):
        self._set_iio_dev_attr_str("h8_mag_corr", value, self.admt4000_ctrl)

    @property
    def h8_phase_corr(self):
        """ADMT4000 8th harmonic correction coefficient phase."""
        return self._get_iio_dev_attr_str("h8_ph_corr", self.admt4000_ctrl)

    @h8_phase_corr.setter
    def h8_phase_corr(self, value):
        self._set_iio_dev_attr_str("h8_ph_corr", value, self.admt4000_ctrl)

    class _channel(attribute):

        """ADMT4000 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADMT4000 channel raw."""
            return float(self._get_iio_attr_str(self.name, "raw", False,  self._ctrl))

        @property
        def scale(self):
            """ADMT4000 channel scale(gain)."""
            return float(self._get_iio_attr_str(self.name, "scale", False, self._ctrl))
        
        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, value,  self._ctrl)

        @property
        def offset(self):
            """ADMT4000 channel offset."""
            return float(self._get_iio_attr_str(self.name, "offset", False,  self._ctrl))

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, value, self._ctrl)
