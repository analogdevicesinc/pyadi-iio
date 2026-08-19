# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import tx_chan_comp_no_buff

# Motor direction constants
CLOCKWISE = 1
COUNTER_CLOCKWISE = -1


class tmc5240(tx_chan_comp_no_buff):
    """TMC5240 36V 2ARMS+ Smart Integrated Stepper Driver and Controller."""

    compatible_parts = ["tmc5240"]
    _complex_data = False
    _control_device_name = "tmc5240"
    _tx_data_device_name = "tmc5240"
    _channel_def = None

    def __init__(self, uri="", direction=CLOCKWISE, **kwargs):
        """tmc5240 class constructor."""
        tx_chan_comp_no_buff.__init__(self, uri=uri, **kwargs)
        self._mot_ctrl = self._ctrl
        self._direction = direction  # CLOCKWISE or COUNTER_CLOCKWISE

        self.angular_position = self._mot_position_channel(
            self._mot_ctrl, "angular_position", output=True, direction=self._direction
        )
        self.angular_velocity = self._mot_velocity_channel(
            self._mot_ctrl, "angular_velocity", output=True, direction=self._direction
        )
        self.angular_acceleration = self._mot_acceleration_channel(
            self._mot_ctrl,
            "angular_acceleration",
            output=True,
            direction=self._direction,
        )

    @property
    def amax(self):
        """TMC5240 Maximum Acceleration."""
        return self._get_iio_dev_attr("amax", self._mot_ctrl)

    @amax.setter
    def amax(self, value):
        self._set_iio_dev_attr("amax", value, self._mot_ctrl)

    @property
    def vmax(self):
        """TMC5240 Maximum Velocity."""
        return self._get_iio_dev_attr("vmax", self._mot_ctrl)

    @vmax.setter
    def vmax(self, value):
        self._set_iio_dev_attr("vmax", value, self._mot_ctrl)

    @property
    def dmax(self):
        """TMC5240 Maximum Deceleration."""
        return self._get_iio_dev_attr("dmax", self._mot_ctrl)

    @dmax.setter
    def dmax(self, value):
        self._set_iio_dev_attr("dmax", value, self._mot_ctrl)

    @property
    def vstart(self):
        """TMC5240 Start velocity."""
        return self._get_iio_dev_attr("vstart", self._mot_ctrl)

    @vstart.setter
    def vstart(self, value):
        self._set_iio_dev_attr("vstart", value, self._mot_ctrl)

    @property
    def a1(self):
        """TMC5240 First acceleration ramp."""
        return self._get_iio_dev_attr("a1", self._mot_ctrl)

    @a1.setter
    def a1(self, value):
        self._set_iio_dev_attr("a1", value, self._mot_ctrl)

    @property
    def v1(self):
        """TMC5240 First velocity ramp."""
        return self._get_iio_dev_attr("v1", self._mot_ctrl)

    @v1.setter
    def v1(self, value):
        self._set_iio_dev_attr("v1", value, self._mot_ctrl)

    @property
    def a2(self):
        """TMC5240 Second acceleration ramp."""
        return self._get_iio_dev_attr("a2", self._mot_ctrl)

    @a2.setter
    def a2(self, value):
        self._set_iio_dev_attr("a2", value, self._mot_ctrl)

    @property
    def v2(self):
        """TMC5240 Second velocity ramp."""
        return self._get_iio_dev_attr("v2", self._mot_ctrl)

    @v2.setter
    def v2(self, value):
        self._set_iio_dev_attr("v2", value, self._mot_ctrl)

    @property
    def d1(self):
        """TMC5240 First deceleration ramp."""
        return self._get_iio_dev_attr("d1", self._mot_ctrl)

    @d1.setter
    def d1(self, value):
        self._set_iio_dev_attr("d1", value, self._mot_ctrl)

    @property
    def d2(self):
        """TMC5240 Second deceleration ramp."""
        return self._get_iio_dev_attr("d2", self._mot_ctrl)

    @d2.setter
    def d2(self, value):
        self._set_iio_dev_attr("d2", value, self._mot_ctrl)

    @property
    def vstop(self):
        """TMC5240 Stop velocity."""
        return self._get_iio_dev_attr("vstop", self._mot_ctrl)

    @vstop.setter
    def vstop(self, value):
        self._set_iio_dev_attr("vstop", value, self._mot_ctrl)

    @property
    def direction(self):
        """TMC5240 Direction of shaft."""
        value = self._get_iio_dev_attr("direction", self._mot_ctrl)
        if value == 0:
            return COUNTER_CLOCKWISE

        return CLOCKWISE

    @direction.setter
    def direction(self, value):
        if value not in [CLOCKWISE, COUNTER_CLOCKWISE]:
            raise ValueError(
                f"Direction must be {CLOCKWISE} (clockwise) or {COUNTER_CLOCKWISE} (counter-clockwise)"
            )

        if value == COUNTER_CLOCKWISE:
            value = 0

        self._set_iio_dev_attr("direction", value, self._mot_ctrl)

    def stop(self):
        """Stop motor motion."""
        self._set_iio_dev_attr("stop", "1", self._mot_ctrl)

    class _mot_channel(attribute):
        """TMC5240 channel."""

        def __init__(self, ctrl, channel_name, output=False, direction=CLOCKWISE):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output
            self._direction = direction  # CLOCKWISE or COUNTER_CLOCKWISE

        @property
        def scale(self):
            """TMC5240 channel scale or gain."""
            return self._get_iio_attr(self.name, "scale", self._output, self._ctrl)

        @property
        def calibscale(self):
            """TMC5240 channel calibscale or gain."""
            return self._get_iio_attr(self.name, "calibscale", self._output, self._ctrl)

        @calibscale.setter
        def calibscale(self, value):
            if value == 0:
                raise ValueError("calibscale cannot be set to 0")
            self._set_iio_attr_float(
                self.name, "calibscale", self._output, value, self._ctrl
            )

        @property
        def processed(self):
            """TMC5240 channel processed value."""
            return self.raw * self.scale * self.calibscale

        @processed.setter
        def processed(self, value):
            divisor = self.scale * self.calibscale
            if divisor == 0:
                raise ZeroDivisionError(
                    "Cannot set processed value: scale * calibscale is zero"
                )
            self.raw = int(value / divisor)

    class _mot_acceleration_channel(_mot_channel):
        """TMC5240 acceleration channel."""

        @property
        def raw(self):
            """TMC5240 raw acceleration value."""
            return self._direction * self._get_iio_attr(
                self.name, "raw", self._output, self._ctrl
            )

        @raw.setter
        def raw(self, value):
            raise NotImplementedError(
                "raw setter is not available for acceleration channel"
            )

    class _mot_velocity_channel(_mot_channel):
        """TMC5240 velocity channel."""

        @property
        def raw(self):
            """TMC5240 channel raw value."""
            return self._direction * int(
                self._get_iio_attr(self.name, "raw", self._output, self._ctrl)
            )

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(
                self.name, "raw", self._output, self._direction * int(value), self._ctrl
            )

    class _mot_position_channel(_mot_velocity_channel):
        """TMC5240 position channel."""

        @property
        def preset(self):
            """TMC5240 preset position value."""
            return self._direction * self._get_iio_attr(
                self.name, "preset", self._output, self._ctrl
            )

        @preset.setter
        def preset(self, value):
            self._set_iio_attr(
                self.name,
                "preset",
                self._output,
                self._direction * int(value),
                self._ctrl,
            )
