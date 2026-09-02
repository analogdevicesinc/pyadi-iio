# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class ad5933(rx_chan_comp):
    """AD5933 1 MSPS, 12-bit impedance converter, network analyzer.

    The attribute names mirror the IIO ABI exposed by the device
    (as reported by ``iio_info``): the sweep configuration lives on the
    ``altvoltage0`` output channel and the input PGA scale on the
    ``voltage0`` input channel, while the measurement/sweep triggers are
    debug attributes.
    """

    compatible_parts = ["ad5933"]
    _complex_data = False
    _control_device_name = "ad5933"
    _rx_data_device_name = "ad5933"
    _channel_def = None
    _device_name = "ad5933"
    _rx_channel_names = ["voltage0", "voltage1"]
    _rx_data_type = np.int16
    _rx_unbuffered_data = False
    _rx_data_si_type = float
    # tinyiiod returns the whole sweep in a single submit() (one block, all
    # points), and its iio_set_buffers_count() rejects any count != 1 with
    # -EINVAL. Request exactly one block so libiio does not negotiate more.
    _rx_buffer_num_blocks = 1

    def __init__(self, uri="", **kwargs):
        """ad5933 class constructor."""
        rx_chan_comp.__init__(self, uri=uri, **kwargs)

        self.real = self._channel(self._ctrl, "voltage0")
        self.imag = self._channel(self._ctrl, "voltage1")
        self.temp = self._temp_channel(self._ctrl, "temp")

    def reg_read(self, addr):
        """Read IIO device register."""
        return self._ctrl.reg_read(addr)

    def reg_write(self, addr, value):
        """Write IIO device register."""
        self._ctrl.reg_write(addr, value)

    #
    # Device (global) attributes
    #
    @property
    def in_voltage0_scale(self):
        """AD5933 input PGA scale. 1 selects a gain of x1, 0.2 selects x5.
        Allowed values are given by ``in_voltage0_scale_available``."""
        return self._get_iio_attr("voltage0", "scale", False, self._ctrl)

    @in_voltage0_scale.setter
    def in_voltage0_scale(self, value):
        self._set_iio_attr("voltage0", "scale", False, value, self._ctrl)

    @property
    def in_voltage0_scale_available(self):
        """AD5933 available input PGA scales (read-only)."""
        return self._get_iio_attr_str("voltage0", "scale_available", False, self._ctrl)

    @property
    def out_altvoltage0_raw(self):
        """AD5933 output excitation amplitude code. Allowed values are given
        by ``out_altvoltage0_scale_available``."""
        return self._get_iio_attr("altvoltage0", "raw", True, self._ctrl)

    @out_altvoltage0_raw.setter
    def out_altvoltage0_raw(self, value):
        self._set_iio_attr("altvoltage0", "raw", True, value, self._ctrl)

    @property
    def out_altvoltage0_scale_available(self):
        """AD5933 available output excitation amplitude codes (read-only)."""
        return self._get_iio_attr_str(
            "altvoltage0", "scale_available", True, self._ctrl
        )

    @property
    def out_altvoltage0_frequency_start(self):
        """AD5933 sweep start frequency in Hz."""
        return self._get_iio_attr("altvoltage0", "frequency_start", True, self._ctrl)

    @out_altvoltage0_frequency_start.setter
    def out_altvoltage0_frequency_start(self, value):
        self._set_iio_attr("altvoltage0", "frequency_start", True, value, self._ctrl)

    @property
    def out_altvoltage0_frequency_increment(self):
        """AD5933 frequency increment per sweep point in Hz."""
        return self._get_iio_attr(
            "altvoltage0", "frequency_increment", True, self._ctrl
        )

    @out_altvoltage0_frequency_increment.setter
    def out_altvoltage0_frequency_increment(self, value):
        self._set_iio_attr(
            "altvoltage0", "frequency_increment", True, value, self._ctrl
        )

    @property
    def out_altvoltage0_frequency_points(self):
        """AD5933 number of frequency points in the sweep."""
        return self._get_iio_attr("altvoltage0", "frequency_points", True, self._ctrl)

    @out_altvoltage0_frequency_points.setter
    def out_altvoltage0_frequency_points(self, value):
        self._set_iio_attr("altvoltage0", "frequency_points", True, value, self._ctrl)

    @property
    def out_altvoltage0_settling_cycles(self):
        """AD5933 number of settling cycles (0-511)."""
        return self._get_iio_attr("altvoltage0", "settling_cycles", True, self._ctrl)

    @out_altvoltage0_settling_cycles.setter
    def out_altvoltage0_settling_cycles(self, value):
        self._set_iio_attr("altvoltage0", "settling_cycles", True, value, self._ctrl)

    #
    # Debug attributes (sweep control / measurement triggers)
    #
    @property
    def sweep_initialized(self):
        """AD5933 sweep initialization status/trigger. Write 1 to initialize a
        sweep with the current start frequency and increment settings."""
        return self._get_iio_debug_attr("sweep_initialized", self._ctrl)

    @sweep_initialized.setter
    def sweep_initialized(self, value):
        self._set_iio_debug_attr_str("sweep_initialized", value, self._ctrl)

    @property
    def sweep_started(self):
        """AD5933 sweep start trigger/status. Write 1 to start the frequency
        sweep; reads back the current sweep state."""
        return self._get_iio_debug_attr("sweep_started", self._ctrl)

    @sweep_started.setter
    def sweep_started(self, value):
        self._set_iio_debug_attr_str("sweep_started", value, self._ctrl)

    @property
    def current_output_frequency(self):
        """AD5933 current excitation output frequency in Hz (read-only)."""
        return self._get_iio_debug_attr("current_output_frequency", self._ctrl)

    @property
    def repeat_measurement(self):
        """AD5933 repeat-measurement trigger. Write 1 to repeat a measurement
        at the current frequency; reads back the current output frequency."""
        return self._get_iio_debug_attr("repeat_measurement", self._ctrl)

    @repeat_measurement.setter
    def repeat_measurement(self, value):
        self._set_iio_debug_attr_str("repeat_measurement", value, self._ctrl)

    @property
    def incremented_measurement(self):
        """AD5933 incremented-measurement trigger. Write 1 to advance to the
        next sweep point and measure; reads back the current output
        frequency."""
        return self._get_iio_debug_attr("incremented_measurement", self._ctrl)

    @incremented_measurement.setter
    def incremented_measurement(self, value):
        self._set_iio_debug_attr_str("incremented_measurement", value, self._ctrl)

    class _channel(attribute):
        """AD5933 raw channel (real / imag)."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD5933 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False, self._ctrl)

    class _temp_channel(_channel):
        """AD5933 temperature channel with scale."""

        @property
        def scale(self):
            """AD5933 temperature channel scale (degC/LSB)."""
            return self._get_iio_attr(self.name, "scale", False, self._ctrl)

        @property
        def processed(self):
            """AD5933 temperature in degrees Celsius."""
            return self.raw * self.scale
