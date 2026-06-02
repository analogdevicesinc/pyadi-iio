# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import logging
from time import sleep

import numpy as np

from adi.admt4000 import admt4000
from adi.attribute import attribute
from adi.rx_tx import shared_def
from adi.tmc5240 import COUNTER_CLOCKWISE, tmc5240


class _admt_evb(shared_def, attribute):
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
        return self._get_iio_dev_attr("pulse_shutdown", self._ctrl)

    @shutdown_pulse.setter
    def shutdown_pulse(self, value):
        self._set_iio_dev_attr("pulse_shutdown", value, self._ctrl)

    @property
    def power_enable(self):
        """Power supply of ADMTxxxx."""
        return self._get_iio_dev_attr("power_enable", self._ctrl)

    @power_enable.setter
    def power_enable(self, value):
        self._set_iio_dev_attr("power_enable", value, self._ctrl)

    @property
    def coil_reset(self):
        """Magnetic Reset of ADMTxxxx Turn count."""
        return self._get_iio_dev_attr("coil_reset", self._ctrl)

    @coil_reset.setter
    def coil_reset(self, value):
        self._set_iio_dev_attr("coil_reset", value, self._ctrl)


class admt4000ard2z(_admt_evb):
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
        _admt_evb.__init__(self, uri)
        self.sensor = admt4000(self._ctx)
        self._disable_dc_dc_after_reset = disable_dc_dc_after_reset
        self._dc_dc_charge_time_ms = dc_dc_charge_time_ms
        self._reset_pulse_time_ms = reset_pulse_time_ms

    @property
    def magnetic_reset(self):
        """Perform Magnetic Reset of ADMT4000 Turn count."""
        return None  # Dummy getter for magnetic_reset property

    @magnetic_reset.setter
    def magnetic_reset(self, value):
        if value:
            logging.info("Performing magnetic reset...")
            self.shutdown_pulse = 0
            sleep(float(self._dc_dc_charge_time_ms) / 1000.0)
            self.coil_reset = 1
            sleep(float(self._reset_pulse_time_ms) / 1000.0)
            self.coil_reset = 0
            if self._disable_dc_dc_after_reset:
                self.shutdown_pulse = 1

            sleep(admt4000._MAGNETIC_RESET_SETTLE_TIME_S)
            logging.info("Magnetic reset complete.")
            self.sensor.reg_write(0x06, 0x0000)
            self.sensor.reinitialize()


class admt4000ard1z(admt4000ard2z):
    """ADMT4000ARD1Z Calibration Kit integrating ADMT4000 with a TMC5240 motor controller."""

    _device_name = "eval_admt4000ard1z"

    def __init__(
        self,
        uri="",
        motor_direction=COUNTER_CLOCKWISE,
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

    @property
    def motor_sensor_alignment(self):
        """Align motor and sensor positions after mechanical coupling."""
        return None  # Dummy getter for motor_sensor_alignment property

    @motor_sensor_alignment.setter
    def motor_sensor_alignment(self, value):
        if value:
            logging.info("Aligning motor and sensor measurements...")
            sensor_angle = self.sensor.angle.processed
            sensor_curr_turns = self.sensor.turns.processed
            sensor_curr_angle = sensor_angle + int(sensor_curr_turns) * 360

            angle_u_steps = sensor_curr_angle / (
                self.motor.angular_position.scale
                * self.motor.angular_position.calibscale
            )
            self.motor.angular_position.preset = angle_u_steps

    def _rotate_absolute(self, angle):
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

    def _rotate_relative(self, angle):
        """Rotate motor to relative angle position."""
        target_usteps = angle / (
            self.motor.angular_position.scale * self.motor.angular_position.calibscale
        )
        self._rotate_relative_usteps(target_usteps)

    def _rotate_relative_usteps(self, usteps):
        """Rotate motor by a relative number of microsteps."""
        target_usteps = self.motor.angular_position.raw + usteps
        self.motor.angular_position.raw = target_usteps
        approx_delay = abs(usteps) * 2 / self.motor.vmax
        logging.info(
            f"Approximate delay for positioning: {round(approx_delay)} seconds"
        )
        sleep(approx_delay)
        self.motor.stop()

    @property
    def rotate_absolute_angle(self):
        """Get absolute angle measurement from sensor."""
        return self.sensor.angle.processed + int(self.sensor.turns.processed) * 360

    @rotate_absolute_angle.setter
    def rotate_absolute_angle(self, value):
        self._rotate_absolute(value)

    @property
    def rotate_relative_angle(self):
        """Get relative angle measurement from sensor."""
        return None  # Dummy getter for relative_angle property

    @rotate_relative_angle.setter
    def rotate_relative_angle(self, value):
        self._rotate_relative(value)

    @property
    def rotate_relative_usteps(self):
        """Get relative microstep position from motor."""
        return None  # Dummy getter for relative_usteps property

    @rotate_relative_usteps.setter
    def rotate_relative_usteps(self, value):
        self._rotate_relative_usteps(value)
