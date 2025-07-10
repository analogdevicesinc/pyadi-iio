# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class tmc5240(context_manager, attribute):
    """TMC5240 36V 2ARMS+ Smart Integrated Stepper Driver and Controller"""

    def __init__(self, uri=""):
        """tmc5240 class constructor."""
        self._device_name = "tmc5240"
        context_manager.__init__(self, uri, self._device_name)
        self.usteps = 256  # usteps per full step
        self.full_step = 0.9  # full step angle in degrees
        self.usteps_offset = 0.0  # offset for usteps
        self.motor_direction = 1  # direction of rotation, 1 for clockwise, -1 for counter-clockwise
        # Select the device matching device_name as working device
        self._mot_ctrl = self._ctx.find_device(self._device_name)

        if self._mot_ctrl is None:
            raise Exception("No compatible device found")

    @property
    def amax(self):
        """TMC5240 Maximum Acceleration."""
        return int(self._get_iio_dev_attr_str("amax", self._mot_ctrl))

    @amax.setter
    def amax(self, value):
        self._set_iio_dev_attr_str("amax", value, self._mot_ctrl)

    @property
    def vmax(self):
        """TMC5240 Maximum Velocity."""
        return int(self._get_iio_dev_attr_str("vmax", self._mot_ctrl))

    @vmax.setter
    def vmax(self, value):
        self._set_iio_dev_attr_str("vmax", value, self._mot_ctrl)

    @property
    def dmax(self):
        """TMC5240 Maximum Deceleration."""
        return int(self._get_iio_dev_attr_str("dmax", self._mot_ctrl))

    @dmax.setter
    def dmax(self, value):
        self._set_iio_dev_attr_str("dmax", value, self._mot_ctrl)

    @property
    def target_pos(self):
        """TMC5240 Target Position"""
        return int(self._get_iio_dev_attr_str("target_pos", self._mot_ctrl))

    @target_pos.setter
    def target_pos(self, value):
        self._set_iio_dev_attr_str("target_pos", value, self._mot_ctrl)
    
    @property
    def target_angle(self):
        """TMC5240 Target Position in degrees."""
        current_usteps = self.usteps_offset + self.motor_direction * int(self.target_pos)
        return current_usteps * self.full_step / self.usteps

    @target_angle.setter
    def target_angle(self, value):
        """Set TMC5240 Target Position in degrees."""
        # value = int(self.motor_direction * value * self.usteps / self.full_step - self.usteps_offset)
        # self.target_pos = value
        value = self.motor_direction * (value * self.usteps / self.full_step - self.usteps_offset)
        self.target_pos = value
    @property
    def current_pos(self):
        """TMC5240 Actual Position."""
        return int(self._get_iio_dev_attr_str("current_pos", self._mot_ctrl))
    
    @property
    def current_angle(self):
        """TMC5240 Actual Position in degrees."""
        current_usteps = self.usteps_offset + self.motor_direction * int(self.current_pos)
        return current_usteps * self.full_step / self.usteps

    @property
    def current_angle_rot(self):
        """TMC5240 Actual Position in degrees."""
        current_usteps = self.usteps_offset + self.motor_direction * int(self.current_pos)
        return (current_usteps % (360 * self.usteps / self.full_step)) * self.full_step / self.usteps

    def stop(self):
        self._set_iio_dev_attr_str("stop", 1, self._mot_ctrl)
    