# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import tx_chan_comp_no_buff


class tmc5240(tx_chan_comp_no_buff):
    """TMC5240 36V 2ARMS+ Smart Integrated Stepper Driver and Controller."""

    compatible_parts = ["tmc5240"]
    _complex_data = False
    _control_device_name = "tmc5240"
    _tx_data_device_name = "tmc5240"
    _channel_def = None

    def __init__(self, uri="", direction=1, **kwargs):
        """tmc5240 class constructor."""
        tx_chan_comp_no_buff.__init__(self, uri=uri, **kwargs)
        self._mot_ctrl = self._ctrl
        self._direction = direction  # 1 for clockwise, -1 for counter-clockwise

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
    def vstart(self):
        """TMC5240 Start velocity."""
        return int(self._get_iio_dev_attr_str("vstart", self._mot_ctrl))

    @vstart.setter
    def vstart(self, value):
        self._set_iio_dev_attr_str("vstart", value, self._mot_ctrl)

    @property
    def a1(self):
        """TMC5240 First acceleration ramp."""
        return int(self._get_iio_dev_attr_str("a1", self._mot_ctrl))

    @a1.setter
    def a1(self, value):
        self._set_iio_dev_attr_str("a1", value, self._mot_ctrl)

    @property
    def v1(self):
        """TMC5240 First velocity ramp."""
        return int(self._get_iio_dev_attr_str("v1", self._mot_ctrl))

    @v1.setter
    def v1(self, value):
        self._set_iio_dev_attr_str("v1", value, self._mot_ctrl)

    @property
    def a2(self):
        """TMC5240 Second acceleration ramp."""
        return int(self._get_iio_dev_attr_str("a2", self._mot_ctrl))

    @a2.setter
    def a2(self, value):
        self._set_iio_dev_attr_str("a2", value, self._mot_ctrl)

    @property
    def v2(self):
        """TMC5240 Second velocity ramp."""
        return int(self._get_iio_dev_attr_str("v2", self._mot_ctrl))

    @v2.setter
    def v2(self, value):
        self._set_iio_dev_attr_str("v2", value, self._mot_ctrl)

    @property
    def d1(self):
        """TMC5240 First deceleration ramp."""
        return int(self._get_iio_dev_attr_str("d1", self._mot_ctrl))

    @d1.setter
    def d1(self, value):
        self._set_iio_dev_attr_str("d1", value, self._mot_ctrl)

    @property
    def d2(self):
        """TMC5240 Second deceleration ramp."""
        return int(self._get_iio_dev_attr_str("d2", self._mot_ctrl))

    @d2.setter
    def d2(self, value):
        self._set_iio_dev_attr_str("d2", value, self._mot_ctrl)

    @property
    def vstop(self):
        """TMC5240 Stop velocity."""
        return int(self._get_iio_dev_attr_str("vstop", self._mot_ctrl))

    @vstop.setter
    def vstop(self, value):
        self._set_iio_dev_attr_str("vstop", value, self._mot_ctrl)

    @property
    def direction(self):
        """TMC5240 Direction of shaft."""
        value = int(self._get_iio_dev_attr_str("direction", self._mot_ctrl))
        if value == 0:
            return -1

        return 1

    @direction.setter
    def direction(self, value):
        if value not in [1, -1]:
            raise ValueError(
                "Direction must be 1 (clockwise) or -1 (counter-clockwise)"
            )

        if value == -1:
            value = 0

        self._set_iio_dev_attr("direction", value, self._mot_ctrl)

    def stop(self):
        """Stop motor motion."""
        self._set_iio_dev_attr_str("stop", "1", self._mot_ctrl)

    class _mot_channel(attribute):
        """TMC5240 channel."""

        def __init__(self, ctrl, channel_name, output=False, direction=1):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output
            self._direction = direction  # 1 for clockwise, -1 for counter-clockwise

        @property
        def scale(self):
            """TMC5240 channel scale or gain."""
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @property
        def calibscale(self):
            """TMC5240 channel calibscale or gain."""
            return float(self._get_iio_attr_str(self.name, "calibscale", self._output))

        @calibscale.setter
        def calibscale(self, value):
            if value == 0:
                raise ValueError("calibscale cannot be set to 0")
            self._set_iio_attr(self.name, "calibscale", self._output, float(value))

        @property
        def processed(self):
            """TMC5240 channel processed value."""
            return self.raw * self.scale * self.calibscale

        @processed.setter
        def processed(self, value):
            self.raw = int(value / (self.scale * self.calibscale))

    class _mot_acceleration_channel(_mot_channel):
        """TMC5240 acceleration channel."""

        @property
        def raw(self):
            """TMC5240 raw acceleration value."""
            return self._direction * int(
                self._get_iio_attr(self.name, "raw", self._output)
            )

        @raw.setter
        def raw(self, value):
            raise AttributeError("raw setter is not available for acceleration channel")

    class _mot_velocity_channel(_mot_channel):
        """TMC5240 velocity channel."""

        @property
        def raw(self):
            """TMC5240 channel raw value."""
            return self._direction * int(
                self._get_iio_attr(self.name, "raw", self._output)
            )

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(
                self.name, "raw", self._output, self._direction * int(value)
            )

    class _mot_position_channel(_mot_velocity_channel):
        """TMC5240 position channel."""

        @property
        def preset(self):
            """TMC5240 preset position value."""
            return self._direction * int(
                self._get_iio_attr_str(self.name, "preset", self._output)
            )

        @preset.setter
        def preset(self, value):
            self._set_iio_attr(
                self.name, "preset", self._output, self._direction * int(value)
            )
