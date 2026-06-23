# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from abc import ABC, abstractmethod

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adis16XXX(rx, context_manager, ABC):

    _complex_data = False

    _rx_channel_names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
        "temp0",
    ]

    _device_name = ""

    """Disable mapping of trigger to RX device."""
    disable_trigger = False

    # @property
    @abstractmethod
    def compatible_parts(self):
        raise NotImplementedError

    def __init__(self, uri="", device_name=None, trigger_name=None):
        context_manager.__init__(self, uri, self._device_name)

        if not device_name:
            device_name = self.compatible_parts[0]

        if device_name not in self.compatible_parts:
            raise Exception(
                "Not a compatible device:"
                + str(device_name)
                + ".Please select from:"
                + str(self.compatible_parts)
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
            for i in self.compatible_parts:
                self._ctrl = self._ctx.find_device(i)
                self._rxadc = self._ctx.find_device(i)
                if self._ctrl is not None:
                    print("Fond device = " + i + ". Will use this device instead.")
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

    #####
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
        """ADIS16480 temperature channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADIS16480 raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """ADIS16480 scale value"""
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def offset(self):
            """ADIS16480 offset value"""
            return self._get_iio_attr(self.name, "offset", False)

    class _pressure_channel(attribute):
        """ADIS16480 pressure channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ADIS16480 raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """ADIS16480 scale value"""
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def calibbias(self):
            """ADIS16480 calibration offset"""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            self._set_iio_attr(self.name, "calibbias", False, value)

    class _magn_channel(_pressure_channel):
        """ADIS16480 magnetometer channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def filter_low_pass_3db_frequency(self):
            """ADIS16480 channel bandwidth"""
            return self._get_iio_attr(self.name, "filter_low_pass_3db_frequency", False)

        @filter_low_pass_3db_frequency.setter
        def filter_low_pass_3db_frequency(self, value):
            self._set_iio_attr(self.name, "filter_low_pass_3db_frequency", False, value)

    class _anglvel_accel_channels(_magn_channel):
        """ADIS16480 gyro and accelerometer channels."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def calibscale(self):
            """ADIS16480 calibscale value"""
            return self._get_iio_attr(self.name, "calibscale", False)

        @calibscale.setter
        def calibscale(self, value):
            self._set_iio_attr(self.name, "calibscale", False, value)

    class _delta_channels(attribute):
        """ADIS16480 delta angle and delta velocity channels."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl


class adis16XXX_with_delta_angl(adis16XXX):
    def __init__(self, uri="", device_name=None, trigger_name=None):
        adis16XXX.__init__(self, uri, device_name, trigger_name)

        self._rx_channel_names.append("deltaangl_x")
        self._rx_channel_names.append("deltaangl_y")
        self._rx_channel_names.append("deltaangl_z")
        self._rx_channel_names.append("deltavelocity_x")
        self._rx_channel_names.append("deltavelocity_y")
        self._rx_channel_names.append("deltavelocity_z")


class adis16XXX_with_mag(adis16XXX):
    def __init__(self, uri="", device_name=None, trigger_name=None):
        adis16XXX.__init__(self, uri, device_name, trigger_name)

        self._rx_channel_names.append("pressure0")
        self._rx_channel_names.append("magn_x")
        self._rx_channel_names.append("magn_y")
        self._rx_channel_names.append("magn_z")
        self.pressure = self._pressure_channel(self._ctrl, "pressure0")
        self.magn_x = self._magn_channel(self._ctrl, "magn_x")
        self.magn_y = self._magn_channel(self._ctrl, "magn_y")
        self.magn_z = self._magn_channel(self._ctrl, "magn_z")

    def get_magn_x(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("magn_x")

    magn_x_conv = property(get_magn_x, None)

    def get_magn_y(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("magn_y")

    magn_y_conv = property(get_magn_y, None)

    def get_magn_z(self):
        """Value returned in radians."""
        return self.__get_scaled_sensor("magn_z")

    magn_z_conv = property(get_magn_z, None)

    def get_pressure(self):
        """Value returned in kilo Pascal."""
        return self.__get_scaled_sensor("pressure0")

    pressure_conv = property(get_pressure, None)

    @property
    def magn_x_calibbias(self):
        """User calibration offset for magnetometer for the x-axis."""
        if self.magn_x:
            return self._get_iio_attr("magn_x", "calibbias", False)
        return 0

    @magn_x_calibbias.setter
    def magn_x_calibbias(self, value):
        if self.magn_x:
            self._set_iio_attr("magn_x", "calibbias", False, value)

    @property
    def magn_y_calibbias(self):
        """User calibration offset for magnetometer for the y-axis."""
        if self.magn_y:
            return self._get_iio_attr("magn_y", "calibbias", False)
        return 0

    @magn_y_calibbias.setter
    def magn_y_calibbias(self, value):
        if self.magn_y:
            self._set_iio_attr("magn_y", "calibbias", False, value)

    @property
    def magn_z_calibbias(self):
        """User calibration offset for magnetometer for the z-axis."""
        if self.magn_z:
            return self._get_iio_attr("magn_z", "calibbias", False)
        return 0

    @magn_z_calibbias.setter
    def magn_z_calibbias(self, value):
        if self.magn_z:
            self._set_iio_attr("magn_z", "calibbias", False, value)

    @property
    def pressure_calibbias(self):
        """User calibration offset for pressure."""
        if self.pressure:
            return self._get_iio_attr("pressure0", "calibbias", False)
        return 0

    @pressure_calibbias.setter
    def pressure_calibbias(self, value):
        if self.pressure:
            self._set_iio_attr("pressure0", "calibbias", False, value)

    @property
    def magn_x_filter_low_pass_3db_frequency(self):
        """Bandwidth for magnetometer for the x-axis."""
        if self.magn_x:
            return self._get_iio_attr("magn_x", "filter_low_pass_3db_frequency", False)
        return 0

    @magn_x_filter_low_pass_3db_frequency.setter
    def magn_x_filter_low_pass_3db_frequency(self, value):
        if self.magn_x:
            self._set_iio_attr("magn_x", "filter_low_pass_3db_frequency", False, value)

    @property
    def magn_y_filter_low_pass_3db_frequency(self):
        """Bandwidth for magnetometer for the y-axis."""
        if self.magn_y:
            return self._get_iio_attr("magn_y", "filter_low_pass_3db_frequency", False)
        return 0

    @magn_y_filter_low_pass_3db_frequency.setter
    def magn_y_filter_low_pass_3db_frequency(self, value):
        if self.magn_y:
            self._set_iio_attr("magn_y", "filter_low_pass_3db_frequency", False, value)

    @property
    def magn_z_filter_low_pass_3db_frequency(self):
        """Bandwidth for magnetometer for the z-axis."""
        if self.magn_z:
            return self._get_iio_attr("magn_z", "filter_low_pass_3db_frequency", False)
        return 0

    @magn_z_filter_low_pass_3db_frequency.setter
    def magn_z_filter_low_pass_3db_frequency(self, value):
        if self.magn_z:
            self._set_iio_attr("magn_z", "filter_low_pass_3db_frequency", False, value)


11


class adis16375(adis16XXX):
    """ADIS16375 Low Profile, Low Noise Six Degrees of Freedom Inertial Sensor

    Args:
        uri: URI of IIO context with ADIS16375 device
        device_name: Name of the device in the IIO context. Default is adis16375
        trigger_name: Name of the trigger in the IIO context. Default is adis16375-dev0
    """

    compatible_parts = ["adis16375"]


class adis16480(adis16XXX_with_mag):
    """ADIS16480 Ten Degrees of Freedom Inertial Sensor with Dynamic Orientation Outputs

    Args:
        uri: URI of IIO context with ADIS16480 device
        device_name: Name of the device in the IIO context. Default is adis16480
        trigger_name: Name of the trigger in the IIO context. Default is adis16480-dev0
    """

    compatible_parts = ["adis16480"]


class adis16485(adis16XXX):
    """ADIS16485 Tactical Grade Six Degrees of Freedom MEMS Inertial Sensor

    Args:
        uri: URI of IIO context with ADIS16485 device
        device_name: Name of the device in the IIO context. Default is adis16485
        trigger_name: Name of the trigger in the IIO context. Default is adis16485-dev0
    """

    compatible_parts = ["adis16485"]


class adis16488(adis16XXX_with_mag):
    """ADIS16488  Tactical Grade Ten Degrees of Freedom Inertial Sensor

    Args:
        uri: URI of IIO context with ADIS16488 device
        device_name: Name of the device in the IIO context. Default is adis16488
        trigger_name: Name of the trigger in the IIO context. Default is adis16488-dev0
    """

    compatible_parts = ["adis16488"]


class adis16490(adis16XXX):
    """ADIS16490 Tactical Grade, Six Degrees of Freedom Inertial Sensor

    Args:
        uri: URI of IIO context with ADIS16490 device
        device_name: Name of the device in the IIO context. Default is adis16490
        trigger_name: Name of the trigger in the IIO context. Default is adis16490-dev0
    """

    compatible_parts = ["adis16490"]


class adis16495(adis16XXX):
    """ADIS16495-X Tactical Grade, Six Degrees of Freedom Inertial Sensor

    This class is compatible with the following parts:
    - adis16495-1
    - adis16495-2
    - adis16495-3

    Args:
        uri: URI of IIO context with ADIS16495 device
        device_name: Name of the device in the IIO context. Default is adis16495-1
        trigger_name: Name of the trigger in the IIO context. Default is adis16495-1-dev0
    """

    compatible_parts = ["adis16495-1", "adis16495-2", "adis16495-3"]


class adis16497(adis16XXX):
    """ADIS16497-X Ten Degrees of Freedom Inertial Sensor with Dynamic Orientation Outputs

    This class is compatible with the following parts:
    - adis16497-1
    - adis16497-2
    - adis16497-3
    """

    compatible_parts = ["adis16497-1", "adis16497-2", "adis16497-3"]


class adis16545(adis16XXX_with_delta_angl):
    """ADIS16545-X Tactical Grade, Six Degrees of Freedom Inertial Sensor

    This class is compatible with the following parts:
    - adis16545-1
    - adis16545-2
    - adis16545-3

    Args:
        uri: URI of IIO context with ADIS16545 device
        device_name: Name of the device in the IIO context. Default is adis16545-1
        trigger_name: Name of the trigger in the IIO context. Default is adis16545-1-dev0
    """

    compatible_parts = ["adis16545-1", "adis16545-2", "adis16545-3"]


class adis16547(adis16XXX_with_delta_angl):
    """ADIS16547-X Tactical Grade, Six Degrees of Freedom Inertial Sensors

    This class is compatible with the following parts:
    - adis16547-1
    - adis16547-2
    - adis16547-3

    Args:
        uri: URI of IIO context with ADIS16547 device
        device_name: Name of the device in the IIO context. Default is adis16547-1
        trigger_name: Name of the trigger in the IIO context. Default is adis16547-1-dev0
    """

    compatible_parts = ["adis16547-1", "adis16547-2", "adis16547-3"]
