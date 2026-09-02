# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import logging
from time import sleep

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class admt4000(rx_chan_comp):
    """ADMT4000 True power-on multiturn sensor."""

    compatible_parts = ["admt4000", "admt4000ard1z", "admt4000ard2z"]
    _complex_data = False
    _control_device_name = "admt4000"
    _rx_data_device_name = "admt4000"
    _channel_def = None
    _device_name = "admt4000"
    _rx_channel_names = ["turns", "angle", "temp", "sine", "cosine", "radius"]
    _rx_data_type = np.int16
    _rx_unbuffered_data = False
    _rx_data_si_type = float

    # Default configuration constants
    _DEFAULT_BUFFER_SIZE = 20  # Default buffer size for sensor data
    _MAGNETIC_RESET_SETTLE_TIME_S = 2.0  # Settle time after magnetic reset

    disable_trigger = False

    def __init__(self, uri="", trigger_name=None, **kwargs):
        """admt4000 class constructor."""
        rx_chan_comp.__init__(self, uri=uri, **kwargs)

        self.turns = self._scaled_channel(self._ctrl, "turns")
        self.angle = self._scaled_channel(self._ctrl, "angle")
        self.temp = self._temp_channel(self._ctrl, "temp")
        self.sine = self._channel(self._ctrl, "sine")
        self.cosine = self._channel(self._ctrl, "cosine")
        self.radius = self._scaled_channel(self._ctrl, "radius")
        self.gpio = self._gpio_accessor(self._ctrl)

        if not self.disable_trigger:
            if not trigger_name:
                trigger_name = self._device_name + "-dev0"
            self._trigger = self._ctx.find_device(trigger_name)
            if self._trigger:
                self._rxadc._set_trigger(self._trigger)

        self.rx_buffer_size = self._DEFAULT_BUFFER_SIZE  # Make default buffer smaller

    def reg_read(self, addr):
        """Read IIO device register."""
        return self._ctrl.reg_read(addr)

    def reg_write(self, addr, value):
        """Write IIO device register."""
        self._ctrl.reg_write(addr, value)

    @property
    def conv_sync_mode(self):
        """ADMT4000 conversion sync mode."""
        return self._get_iio_dev_attr("conv_sync_mode", self._ctrl)

    @conv_sync_mode.setter
    def conv_sync_mode(self, value):
        self._set_iio_dev_attr("conv_sync_mode", value, self._ctrl)

    @property
    def conv_sync_mode_available(self):
        """ADMT4000 available conversion sync modes."""
        return self._get_iio_dev_attr("conv_sync_mode_available", self._ctrl)

    @property
    def angle_filter_enable(self):
        """ADMT4000 angle filter enable."""
        return self._get_iio_dev_attr("angle_filter_enable", self._ctrl)

    @angle_filter_enable.setter
    def angle_filter_enable(self, value):
        self._set_iio_dev_attr("angle_filter_enable", value, self._ctrl)

    @property
    def conversion_mode(self):
        """ADMT4000 conversion mode."""
        return self._get_iio_dev_attr("conversion_mode", self._ctrl)

    @conversion_mode.setter
    def conversion_mode(self, value):
        self._set_iio_dev_attr("conversion_mode", value, self._ctrl)

    @property
    def h8_corr_src(self):
        """ADMT4000 8th harmonic correction source."""
        return self._get_iio_dev_attr("h8_corr_src", self._ctrl)

    @h8_corr_src.setter
    def h8_corr_src(self, value):
        self._set_iio_dev_attr("h8_corr_src", value, self._ctrl)

    @property
    def h8_corr_src_available(self):
        """ADMT4000 available 8th harmonic correction sources."""
        return self._get_iio_dev_attr("h8_corr_src_available", self._ctrl)

    @property
    def harmonics(self):
        """ADMT4000 1st, 2nd, 3rd, and 8th harmonic correction values. Passed as list of tuples of (magnitude, phase)."""
        harmonics_raw = self._get_iio_dev_attr_str("harmonics", self._ctrl)
        harmonics_mag_scale = self._get_iio_dev_attr(
            "harmonics_magnitude_scale", self._ctrl
        )
        harmonics_phase_scale = self._get_iio_dev_attr(
            "harmonics_phase_scale", self._ctrl
        )
        harmonics_values = []
        values = harmonics_raw.split()
        for i in range(0, len(values), 2):
            if i + 1 < len(values):
                magnitude = float(values[i]) * float(harmonics_mag_scale)
                phase = float(values[i + 1]) * float(harmonics_phase_scale)
                harmonics_values.append((magnitude, phase))
        return harmonics_values

    @harmonics.setter
    def harmonics(self, value):
        if not isinstance(value, list):
            raise ValueError("Input must be a list")

        if not value:
            raise ValueError("Input list cannot be empty")

        # Determine if it's a list of tuples or a list of numbers
        is_tuple_format = isinstance(value[0], tuple)

        if is_tuple_format:
            if len(value) != 4:
                raise ValueError(
                    "Input list must contain exactly 4 (magnitude, phase) tuples"
                )
            for item in value:
                if not isinstance(item, tuple) or len(item) != 2:
                    raise ValueError(
                        "Each tuple must contain exactly 2 numbers (magnitude, phase)"
                    )
                if not all(isinstance(v, (int, float)) for v in item):
                    raise ValueError("All tuple elements must be numbers")
        else:
            if len(value) != 8:
                raise ValueError(
                    "Input list must contain exactly 8 numbers or 4 tuples"
                )
            if not all(isinstance(item, (int, float)) for item in value):
                raise ValueError("All elements must be numbers")

        harmonics_mag_scale = self._get_iio_dev_attr(
            "harmonics_magnitude_scale", self._ctrl
        )
        harmonics_phase_scale = self._get_iio_dev_attr(
            "harmonics_phase_scale", self._ctrl
        )

        flattened = []
        if is_tuple_format:
            for mag, phase in value:
                mag = int(float(mag) / float(harmonics_mag_scale))
                phase = int(float(phase) / float(harmonics_phase_scale))
                flattened.extend([mag, phase])
        else:
            for i, val in enumerate(value):
                scale = harmonics_mag_scale if i % 2 == 0 else harmonics_phase_scale
                flattened.append(int(float(val) / float(scale)))

        value = " ".join(map(str, flattened))
        self._set_iio_dev_attr("harmonics", value, self._ctrl)

    @property
    def faults(self):
        """ADMT4000 device faults status."""
        return self._get_iio_dev_attr("faults", self._ctrl)

    def reinitialize(self):
        """Reinitialize the device after magnetic reset."""
        self._set_iio_dev_attr("reinitialize", 1, self._ctrl)

    class _gpio_accessor(attribute):
        """List-like accessor for ADMT4000 GPIO raw values."""

        _NUM_GPIO = 6  # ADMT4000 has 6 general-purpose input/output pins

        def __init__(self, ctrl):
            self._ctrl = ctrl

        def __getitem__(self, index):
            if not 0 <= index < self._NUM_GPIO:
                raise IndexError(
                    f"GPIO index {index} out of range (0-{self._NUM_GPIO - 1})"
                )
            return self._get_iio_dev_attr(f"gpio{index}_raw", self._ctrl)

        def __setitem__(self, index, value):
            if not 0 <= index < self._NUM_GPIO:
                raise IndexError(
                    f"GPIO index {index} out of range (0-{self._NUM_GPIO - 1})"
                )
            self._set_iio_dev_attr(f"gpio{index}_raw", value, self._ctrl)

        def __len__(self):
            return self._NUM_GPIO

        def __iter__(self):
            for i in range(self._NUM_GPIO):
                yield self[i]

    class _channel(attribute):
        """ADMT4000 channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADMT4000 channel raw."""
            return self._get_iio_attr(self.name, "raw", False, self._ctrl)

    class _scaled_channel(_channel):
        """ADMT4000 scaled channel with scale attribute."""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def scale(self):
            """ADMT4000 channel scale or gain."""
            return self._get_iio_attr(self.name, "scale", False, self._ctrl)

        @property
        def processed(self):
            """ADMT4000 channel processed value."""
            try:
                scale = self.scale
            except (KeyError, AttributeError):
                raise ValueError("Scale attribute not found for channel " + self.name)

            return self.raw * scale

    class _temp_channel(_scaled_channel):
        """ADMT4000 temperature channel."""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def offset(self):
            """ADMT4000 temperature channel offset."""
            return self._get_iio_attr(self.name, "offset", False, self._ctrl)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, value, self._ctrl)

        @property
        def processed(self):
            """ADMT4000 temperature channel processed value."""
            try:
                offset = self.offset
            except (KeyError, AttributeError):
                raise ValueError("Temperature offset attribute not found")

            try:
                scale = self.scale
            except (KeyError, AttributeError):
                raise ValueError("Temperature scale attribute not found")

            return (self.raw + offset) * scale
