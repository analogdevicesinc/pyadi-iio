# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import logging
from time import sleep

import numpy as np

from adi.attribute import attribute
from adi.device_base import rx_chan_comp
from adi.rx_tx import shared_def
from adi.tmc5240 import tmc5240


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
            self._rxadc._set_trigger(self._trigger)

        self.rx_buffer_size = 20  # Make default buffer smaller

    def reg_read(self, addr):
        """Read IIO device register."""
        return self._ctrl.reg_read(addr)

    def reg_write(self, addr, value):
        """Write IIO device register."""
        self._ctrl.reg_write(addr, value)

    @property
    def conv_sync_mode(self):
        """ADMT4000 conversion sync mode."""
        return self._get_iio_dev_attr_str("conv_sync_mode", self._ctrl)

    @conv_sync_mode.setter
    def conv_sync_mode(self, value):
        self._set_iio_dev_attr_str("conv_sync_mode", value, self._ctrl)

    @property
    def conv_sync_mode_available(self):
        """ADMT4000 available conversion sync modes."""
        return self._get_iio_dev_attr_str("conv_sync_mode_available", self._ctrl)

    @property
    def angle_filter_enable(self):
        """ADMT4000 angle filter enable."""
        return self._get_iio_dev_attr_str("angle_filter_enable", self._ctrl)

    @angle_filter_enable.setter
    def angle_filter_enable(self, value):
        self._set_iio_dev_attr_str("angle_filter_enable", value, self._ctrl)

    @property
    def conversion_mode(self):
        """ADMT4000 conversion mode."""
        return self._get_iio_dev_attr_str("conversion_mode", self._ctrl)

    @conversion_mode.setter
    def conversion_mode(self, value):
        self._set_iio_dev_attr_str("conversion_mode", value, self._ctrl)

    @property
    def h8_corr_src(self):
        """ADMT4000 8th harmonic correction source."""
        return self._get_iio_dev_attr_str("h8_corr_src", self._ctrl)

    @h8_corr_src.setter
    def h8_corr_src(self, value):
        self._set_iio_dev_attr_str("h8_corr_src", value, self._ctrl)

    @property
    def h8_corr_src_available(self):
        """ADMT4000 available 8th harmonic correction sources."""
        return self._get_iio_dev_attr_str("h8_corr_src_available", self._ctrl)

    @property
    def harmonics(self):
        """ADMT4000 1st, 2nd, 3rd, and 8th harmonic correction values. Passed as list of tuples of (magnitude, phase)."""
        harmonics_raw = self._get_iio_dev_attr_str("harmonics", self._ctrl)
        harmonics_mag_scale = self._get_iio_dev_attr_str(
            "harmonics_magnitude_scale", self._ctrl
        )
        harmonics_phase_scale = self._get_iio_dev_attr_str(
            "harmonics_phase_scale", self._ctrl
        )
        harmonics_values = []
        values = harmonics_raw.replace(",", " ").split()
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

        harmonics_mag_scale = float(
            self._get_iio_dev_attr_str("harmonics_magnitude_scale", self._ctrl)
        )
        harmonics_phase_scale = float(
            self._get_iio_dev_attr_str("harmonics_phase_scale", self._ctrl)
        )

        flattened = []
        if is_tuple_format:
            for mag, phase in value:
                mag = int(mag / harmonics_mag_scale)
                phase = int(phase / harmonics_phase_scale)
                flattened.extend([mag, phase])
        else:
            for i, val in enumerate(value):
                scale = harmonics_mag_scale if i % 2 == 0 else harmonics_phase_scale
                flattened.append(int(val / scale))

        value = " ".join(map(str, flattened))
        self._set_iio_dev_attr_str("harmonics", value, self._ctrl)

    @property
    def faults(self):
        """ADMT4000 device faults status."""
        return int(self._get_iio_dev_attr_str("faults", self._ctrl))

    def reinitialize(self):
        """Reinitialize the device after magnetic reset."""
        self._set_iio_dev_attr_str("reinitialize", "1", self._ctrl)

    class _gpio_accessor(attribute):
        """List-like accessor for ADMT4000 GPIO raw values."""

        _NUM_GPIO = 6

        def __init__(self, ctrl):
            self._ctrl = ctrl

        def __getitem__(self, index):
            if not 0 <= index < self._NUM_GPIO:
                raise IndexError(
                    f"GPIO index {index} out of range (0-{self._NUM_GPIO - 1})"
                )
            return self._get_iio_dev_attr_str(f"gpio{index}_raw", self._ctrl)

        def __setitem__(self, index, value):
            if not 0 <= index < self._NUM_GPIO:
                raise IndexError(
                    f"GPIO index {index} out of range (0-{self._NUM_GPIO - 1})"
                )
            self._set_iio_dev_attr_str(f"gpio{index}_raw", value, self._ctrl)

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
            return int(self._get_iio_attr_str(self.name, "raw", False, self._ctrl))

    class _scaled_channel(_channel):
        """ADMT4000 scaled channel with scale attribute."""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def scale(self):
            """ADMT4000 channel scale or gain."""
            return float(self._get_iio_attr_str(self.name, "scale", False, self._ctrl))

        @property
        def processed(self):
            """ADMT4000 channel processed value."""
            scale = 1

            try:
                scale = self.scale
            except (KeyError, AttributeError):
                pass

            return self.raw * scale

    class _temp_channel(_scaled_channel):
        """ADMT4000 temperature channel."""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def offset(self):
            """ADMT4000 temperature channel offset."""
            return float(self._get_iio_attr_str(self.name, "offset", False, self._ctrl))

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, value, self._ctrl)

        @property
        def processed(self):
            """ADMT4000 temperature channel processed value."""
            offset = 0
            scale = 1
            try:
                offset = self.offset
            except (KeyError, AttributeError):
                pass

            try:
                scale = self.scale
            except (KeyError, AttributeError):
                pass

            return (self.raw + offset) * scale


class admt_evb(shared_def, attribute):
    """ADMTxxxx ARDUINO-Based Evaluation Board."""

    compatible_parts = ["admt_evb"]
    _complex_data = False
    _control_device_name = "admt_evb"
    _device_name = "admt_evb"

    def __init__(self, uri=""):
        """admt_evb class constructor."""
        shared_def.__init__(self, uri=uri)

    @property
    def shutdown_pulse(self):
        """Shutdown ADMTxxxx Coil Pulse Circuit."""
        return int(self._get_iio_dev_attr_str("pulse_shutdown", self._ctrl))

    @shutdown_pulse.setter
    def shutdown_pulse(self, value):
        self._set_iio_dev_attr_str("pulse_shutdown", value, self._ctrl)

    @property
    def power_enable(self):
        """Power supply of ADMTxxxx."""
        return int(self._get_iio_dev_attr_str("power_enable", self._ctrl))

    @power_enable.setter
    def power_enable(self, value):
        self._set_iio_dev_attr_str("power_enable", value, self._ctrl)

    @property
    def coil_reset(self):
        """Magnetic Reset of ADMTxxxx Turn count."""
        return int(self._get_iio_dev_attr_str("coil_reset", self._ctrl))

    @coil_reset.setter
    def coil_reset(self, value):
        self._set_iio_dev_attr_str("coil_reset", value, self._ctrl)


class admt4000ard2z(admt_evb):
    """ADMT4000ARD2Z ADMT4000 kit."""

    _device_name = "eval_admt4000ard2z"

    def __init__(
        self,
        uri="",
        disable_dc_dc_after_reset=True,
        dc_dc_charge_time_ms=100,
        reset_pulse_time_ms=100,
    ):
        """admt4000ard2z class constructor."""
        admt_evb.__init__(self, uri)
        self.sensor = admt4000(self._ctx)
        self._disable_dc_dc_after_reset = disable_dc_dc_after_reset
        self._dc_dc_charge_time_ms = dc_dc_charge_time_ms
        self._reset_pulse_time_ms = reset_pulse_time_ms

    def magnetic_reset(self):
        """Perform Magnetic Reset of ADMT4000 Turn count."""
        logging.info("Performing magnetic reset...")
        self.shutdown_pulse = 0
        sleep(self._dc_dc_charge_time_ms / 1000)
        self.coil_reset = 1
        sleep(self._reset_pulse_time_ms / 1000)
        self.coil_reset = 0
        if self._disable_dc_dc_after_reset:
            self.shutdown_pulse = 1

        sleep(2)
        logging.info("Magnetic reset complete.")
        self.sensor.reg_write(0x06, 0x0000)
        self.sensor.reinitialize()


class admt4000ard1z(admt4000ard2z):
    """ADMT4000ARD1Z Calibration Kit integrating ADMT4000 with a TMC5240 motor controller."""

    _device_name = "eval_admt4000ard1z"

    def __init__(
        self,
        uri="",
        motor_direction=-1,
        disable_dc_dc_after_reset=True,
        dc_dc_charge_time_ms=100,
        reset_pulse_time_ms=100,
    ):
        """admt4000ard1z class constructor."""
        admt4000ard2z.__init__(
            self,
            uri,
            disable_dc_dc_after_reset,
            dc_dc_charge_time_ms,
            reset_pulse_time_ms,
        )
        self.motor = tmc5240(self._ctx, direction=motor_direction)

    def motor_sensor_alignment(self):
        """Align motor and sensor positions after mechanical coupling."""
        logging.info("Aligning motor and sensor measurements...")
        sensor_angle = self.sensor.angle.processed
        sensor_curr_turns = self.sensor.turns.processed
        sensor_curr_angle = sensor_angle + int(sensor_curr_turns) * 360

        angle_u_steps = (sensor_curr_angle) / (
            self.motor.angular_position.scale * self.motor.angular_position.calibscale
        )

        self.motor.angular_position.preset = angle_u_steps

    def rotate_absolute(self, angle):
        """Rotate motor to absolute angle position."""
        target_usteps = angle / (
            self.motor.angular_position.scale * self.motor.angular_position.calibscale
        )
        current_usteps = self.motor.angular_position.raw
        self.motor.angular_position.processed = angle
        approx_delay = abs(target_usteps - current_usteps) * 2 / self.motor.vmax
        logging.info(
            f"Approximate delay for positioning: {round(approx_delay)} seconds"
        )
        sleep(approx_delay)
        self.motor.stop()

    def rotate_relative(self, angle):
        """Rotate motor to relative angle position."""
        target_usteps = angle / (
            self.motor.angular_position.scale * self.motor.angular_position.calibscale
        )
        self.rotate_relative_usteps(target_usteps)

    def rotate_relative_usteps(self, usteps):
        """Rotate motor by a relative number of microsteps."""
        target_usteps = self.motor.angular_position.raw + usteps
        self.motor.angular_position.raw = target_usteps
        approx_delay = abs(usteps) * 2 / self.motor.vmax
        logging.info(
            f"Approximate delay for positioning: {round(approx_delay)} seconds"
        )
        sleep(approx_delay)
        self.motor.stop()
