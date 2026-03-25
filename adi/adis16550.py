# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adis16550(rx, context_manager):
    _complex_data = False

    _rx_channel_names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
        "temp0",
        "deltaangl_x",
        "deltaangl_y",
        "deltaangl_z",
        "deltavelocity_x",
        "deltavelocity_y",
        "deltavelocity_z",
    ]

    _device_name = ""

    """Disable mapping of trigger to RX device."""
    disable_trigger = False

    def __init__(self, uri="", device_name=None, trigger_name=None):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["adis16550"]

        if not device_name:
            device_name = compatible_parts[0]

        if device_name not in compatible_parts:
            raise Exception(
                "Not a compatible device:"
                + str(device_name)
                + ".Please select from:"
                + str(compatible_parts)
            )
        else:
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)
            if not trigger_name:
                trigger_name = device_name + "-dev0"

        if self._ctrl is None:
            print(
                "No device found with device_name = "
                + device_name
                + ". Searching for a device found in the compatible list."
            )
            for i in compatible_parts:
                self._ctrl = self._ctx.find_device(i)
                self._rxadc = self._ctx.find_device(i)
                if self._ctrl is not None:
                    print("Found device = " + i + ". Will use this device instead.")
                    break
            if self._ctrl is None:
                raise Exception("No compatible device found")

        self.anglvel_x = self._anglvel_accel_channels(self._ctrl, "anglvel_x")
        self.anglvel_y = self._anglvel_accel_channels(self._ctrl, "anglvel_y")
        self.anglvel_z = self._anglvel_accel_channels(self._ctrl, "anglvel_z")
        self.accel_x = self._anglvel_accel_channels(self._ctrl, "accel_x")
        self.accel_y = self._anglvel_accel_channels(self._ctrl, "accel_y")
        self.accel_z = self._anglvel_accel_channels(self._ctrl, "accel_z")
        self.temp = self._temp_channel(self._ctrl, "temp0")
        self.deltaangl_x = self._delta_channels(self._ctrl, "deltaangl_x")
        self.deltaangl_y = self._delta_channels(self._ctrl, "deltaangl_y")
        self.deltaangl_z = self._delta_channels(self._ctrl, "deltaangl_z")
        self.deltavelocity_x = self._delta_channels(self._ctrl, "deltavelocity_x")
        self.deltavelocity_y = self._delta_channels(self._ctrl, "deltavelocity_y")
        self.deltavelocity_z = self._delta_channels(self._ctrl, "deltavelocity_z")

        # Set default trigger
        if not self.disable_trigger:
            self._trigger = self._ctx.find_device(trigger_name)
            self._rxadc._set_trigger(self._trigger)

        rx.__init__(self)
        self.rx_buffer_size = 16  # Make default buffer smaller

    def __get_scaled_sensor(self, channel_name: str) -> float:
        raw = self._get_iio_attr(channel_name, "raw", False)
        scale = self._get_iio_attr(channel_name, "scale", False)

        return raw * scale

    def __get_scaled_sensor_temp(self, channel_name: str) -> float:
        raw = self._get_iio_attr(channel_name, "raw", False)
        scale = self._get_iio_attr(channel_name, "scale", False)
        offset = self._get_iio_attr(channel_name, "offset", False)

        return (raw + offset) * scale

    def get_anglvel_x(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_x")

    anglvel_x_conv = property(get_anglvel_x, None)

    def get_anglvel_y(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_y")

    anglvel_y_conv = property(get_anglvel_y, None)

    def get_anglvel_z(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_z")

    anglvel_z_conv = property(get_anglvel_z, None)

    def get_accel_x(self):
        """Value returned in meters per squared second."""
        return self.__get_scaled_sensor("accel_x")

    accel_x_conv = property(get_accel_x, None)

    def get_accel_y(self):
        """Value returned in meters per squared second."""
        return self.__get_scaled_sensor("accel_y")

    accel_y_conv = property(get_accel_y, None)

    def get_accel_z(self):
        """Value returned in meters per squared second."""
        return self.__get_scaled_sensor("accel_z")

    accel_z_conv = property(get_accel_z, None)

    def get_temp(self):
        """Value returned in millidegrees Celsius."""
        return self.__get_scaled_sensor_temp("temp0")

    temp_conv = property(get_temp, None)

    def get_deltaangl_x(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("deltaangl_x")

    deltaangl_x_conv = property(get_deltaangl_x, None)

    def get_deltaangl_y(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("deltaangl_y")

    deltaangl_y_conv = property(get_deltaangl_y, None)

    def get_deltaangl_z(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("deltaangl_z")

    deltaangl_z_conv = property(get_deltaangl_z, None)

    def get_deltavelocity_x(self):
        """Value returned in meters per second."""
        return self.__get_scaled_sensor("deltavelocity_x")

    deltavelocity_x_conv = property(get_deltavelocity_x, None)

    def get_deltavelocity_y(self):
        """Value returned in meters per second."""
        return self.__get_scaled_sensor("deltavelocity_y")

    deltavelocity_y_conv = property(get_deltavelocity_y, None)

    def get_deltavelocity_z(self):
        """Value returned in meters per second."""
        return self.__get_scaled_sensor("deltavelocity_z")

    deltavelocity_z_conv = property(get_deltavelocity_z, None)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def current_timestamp_clock(self):
        """current_timestamp_clock: Source clock for timestamps"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    @current_timestamp_clock.setter
    def current_timestamp_clock(self, value):
        self._set_iio_dev_attr_str("current_timestamp_clock", value)

    @property
    def anglvel_x_calibbias(self):
        """User calibration offset for gyroscope for the x-axis."""
        return self._get_iio_attr("anglvel_x", "calibbias", False)

    @anglvel_x_calibbias.setter
    def anglvel_x_calibbias(self, value):
        self._set_iio_attr("anglvel_x", "calibbias", False, value)

    @property
    def anglvel_y_calibbias(self):
        """User calibration offset for gyroscope for the y-axis."""
        return self._get_iio_attr("anglvel_y", "calibbias", False)

    @anglvel_y_calibbias.setter
    def anglvel_y_calibbias(self, value):
        self._set_iio_attr("anglvel_y", "calibbias", False, value)

    @property
    def anglvel_z_calibbias(self):
        """User calibration offset for gyroscope for the z-axis."""
        return self._get_iio_attr("anglvel_z", "calibbias", False)

    @anglvel_z_calibbias.setter
    def anglvel_z_calibbias(self, value):
        self._set_iio_attr("anglvel_z", "calibbias", False, value)

    @property
    def accel_x_calibbias(self):
        """User calibration offset for accelerometer for the x-axis."""
        return self._get_iio_attr("accel_x", "calibbias", False)

    @accel_x_calibbias.setter
    def accel_x_calibbias(self, value):
        self._set_iio_attr("accel_x", "calibbias", False, value)

    @property
    def accel_y_calibbias(self):
        """User calibration offset for accelerometer for the y-axis."""
        return self._get_iio_attr("accel_y", "calibbias", False)

    @accel_y_calibbias.setter
    def accel_y_calibbias(self, value):
        self._set_iio_attr("accel_y", "calibbias", False, value)

    @property
    def accel_z_calibbias(self):
        """User calibration offset for accelerometer for the z-axis."""
        return self._get_iio_attr("accel_z", "calibbias", False)

    @accel_z_calibbias.setter
    def accel_z_calibbias(self, value):
        self._set_iio_attr("accel_z", "calibbias", False, value)

    @property
    def anglvel_x_calibscale(self):
        """Calibscale value for gyroscope for the x-axis."""
        return self._get_iio_attr("anglvel_x", "calibscale", False)

    @anglvel_x_calibscale.setter
    def anglvel_x_calibscale(self, value):
        self._set_iio_attr("anglvel_x", "calibscale", False, value)

    @property
    def anglvel_y_calibscale(self):
        """Calibscale value for gyroscope for the y-axis."""
        return self._get_iio_attr("anglvel_y", "calibscale", False)

    @anglvel_y_calibscale.setter
    def anglvel_y_calibscale(self, value):
        self._set_iio_attr("anglvel_y", "calibscale", False, value)

    @property
    def anglvel_z_calibscale(self):
        """Calibscale value for gyroscope for the z-axis."""
        return self._get_iio_attr("anglvel_z", "calibscale", False)

    @anglvel_z_calibscale.setter
    def anglvel_z_calibscale(self, value):
        self._set_iio_attr("anglvel_z", "calibscale", False, value)

    @property
    def accel_x_calibscale(self):
        """Calibscale value for accelerometer for the x-axis."""
        return self._get_iio_attr("accel_x", "calibscale", False)

    @accel_x_calibscale.setter
    def accel_x_calibscale(self, value):
        self._set_iio_attr("accel_x", "calibscale", False, value)

    @property
    def accel_y_calibscale(self):
        """Calibcale value for accelerometer for the y-axis."""
        return self._get_iio_attr("accel_y", "calibscale", False)

    @accel_y_calibscale.setter
    def accel_y_calibscale(self, value):
        self._set_iio_attr("accel_y", "calibscale", False, value)

    @property
    def accel_z_calibscale(self):
        """Calibscale for accelerometer for the z-axis."""
        return self._get_iio_attr("accel_z", "calibscale", False)

    @accel_z_calibscale.setter
    def accel_z_calibscale(self, value):
        self._set_iio_attr("accel_z", "calibscale", False, value)

    @property
    def anglvel_x_filter_low_pass_3db_frequency(self):
        """Bandwidth for gyroscope for the x-axis."""
        return self._get_iio_attr("anglvel_x", "filter_low_pass_3db_frequency", False)

    @anglvel_x_filter_low_pass_3db_frequency.setter
    def anglvel_x_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("anglvel_x", "filter_low_pass_3db_frequency", False, value)

    @property
    def anglvel_y_filter_low_pass_3db_frequency(self):
        """Bandwidth for gyroscope for the y-axis."""
        return self._get_iio_attr("anglvel_y", "filter_low_pass_3db_frequency", False)

    @anglvel_y_filter_low_pass_3db_frequency.setter
    def anglvel_y_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("anglvel_y", "filter_low_pass_3db_frequency", False, value)

    @property
    def anglvel_z_filter_low_pass_3db_frequency(self):
        """Bandwidth for gyroscope for the z-axis."""
        return self._get_iio_attr("anglvel_z", "filter_low_pass_3db_frequency", False)

    @anglvel_z_filter_low_pass_3db_frequency.setter
    def anglvel_z_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("anglvel_z", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_x_filter_low_pass_3db_frequency(self):
        """Bandwidth for accelerometer for the x-axis."""
        return self._get_iio_attr("accel_x", "filter_low_pass_3db_frequency", False)

    @accel_x_filter_low_pass_3db_frequency.setter
    def accel_x_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_x", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_y_filter_low_pass_3db_frequency(self):
        """Bandwidth for accelerometer for the y-axis."""
        return self._get_iio_attr("accel_y", "filter_low_pass_3db_frequency", False)

    @accel_y_filter_low_pass_3db_frequency.setter
    def accel_y_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_y", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_z_filter_low_pass_3db_frequency(self):
        """Bandwidth for accelerometer for the z-axis."""
        return self._get_iio_attr("accel_z", "filter_low_pass_3db_frequency", False)

    @accel_z_filter_low_pass_3db_frequency.setter
    def accel_z_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_z", "filter_low_pass_3db_frequency", False, value)

    @property
    def firmware_revision(self):
        """firmware_revision: the firmware revision for the internal firmware"""
        return self._get_iio_debug_attr_str("firmware_revision")

    @property
    def firmware_date(self):
        """firmware_date: the factory configuration date"""
        return self._get_iio_debug_attr_str("firmware_date")

    @property
    def product_id(self):
        """product_id: the numerical portion of the device number"""
        return self._get_iio_debug_attr("product_id")

    @property
    def serial_number(self):
        """serial_number: lot specific serial number"""
        return self._get_iio_debug_attr_str("serial_number")

    @property
    def flash_count(self):
        """flash_counter: flash memory write count"""
        return self._get_iio_debug_attr("flash_count")

    class _temp_channel(attribute):
        """ADIS16550 temperature channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADIS16550 raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """ADIS16550 scale value"""
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def offset(self):
            """ADIS16550 offset value"""
            return self._get_iio_attr(self.name, "offset", False)

    class _simple_channel(attribute):
        """ADIS16550 basic channel, only scale an raw values"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADIS16550 raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """ADIS16550 scale value"""
            return self._get_iio_attr(self.name, "scale", False)

    class _extended_channel(_simple_channel):
        """ADIS16550 pressure channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def calibbias(self):
            """ADIS16550 calibration offset"""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            self._set_iio_attr(self.name, "calibbias", False, value)

        @property
        def calibscale(self):
            """ADIS16550 calibration scale"""
            return self._get_iio_attr(self.name, "calibscale", False)

        @calibscale.setter
        def calibscale(self, value):
            self._set_iio_attr(self.name, "calibscale", False, value)

        @property
        def filter_low_pass_3db_frequency(self):
            """ADIS16550 channel bandwidth"""
            return self._get_iio_attr(self.name, "filter_low_pass_3db_frequency", False)

        @filter_low_pass_3db_frequency.setter
        def filter_low_pass_3db_frequency(self, value):
            self._set_iio_attr(self.name, "filter_low_pass_3db_frequency", False, value)

    class _anglvel_accel_channels(_extended_channel):
        """ADIS16550 gyro and accelerometer channels."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

    class _delta_channels(_simple_channel):
        """ADIS16550 delta angle and delta velocity channels."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl
