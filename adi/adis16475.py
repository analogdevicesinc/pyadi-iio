# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class adis16475_channel_with_offset(attribute):
    """Channel with offset"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def calibbias(self):
        """ADIS165x channel offset"""
        return self._get_iio_attr(self.name, "calibbias", False)

    @calibbias.setter
    def calibbias(self, value):
        self._set_iio_attr(self.name, "calibbias", False, value)

    @property
    def raw(self):
        """ADIS165x channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """ADIS165x channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))


class adis16475_channel(attribute):
    """Channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """ADIS165x channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """ADIS165x channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))


class adis16475(rx_chan_comp):
    """ADIS16475 Compact, Precision, Six Degrees of Freedom Inertial Sensor"""

    _complex_data = False
    _device_name = ""
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
    # timestamp has no scale attribute, keep it out of the channel list.
    _ignore_channels = ["timestamp"]
    compatible_parts = [
        "adis16505-2",
        "adis16470",
        "adis16475-1",
        "adis16475-2",
        "adis16475-3",
        "adis16477-1",
        "adis16477-2",
        "adis16477-3",
        "adis16465-1",
        "adis16465-2",
        "adis16465-3",
        "adis16467-1",
        "adis16467-2",
        "adis16467-3",
        "adis16500",
        "adis16501",
        "adis16505-1",
        "adis16505-3",
        "adis16507-1",
        "adis16507-2",
        "adis16507-3",
        "adis16575-2",
        "adis16575-3",
        "adis16576-2",
        "adis16576-3",
        "adis16577-2",
        "adis16577-3",
    ]

    def __init__(self, uri="", device_name="adis16505-2", device_index=0):
        super().__init__(uri=uri, device_name=device_name, device_index=device_index)

    def __post_init__(self):
        # Set default trigger
        trigger_name = self._ctrl.name + "-dev0"
        self._trigger = self._ctx.find_device(trigger_name)
        self._rxadc._set_trigger(self._trigger)
        # The temperature channel uses the "temp0" IIO id but is exposed as
        # ``temp`` for backwards compatibility.
        self.temp = adis16475_channel(self._ctrl, "temp0")
        self.rx_buffer_size = 16  # Make default buffer smaller

    def _channel_def(self, ctrl, name):
        if name.startswith("anglvel") or name.startswith("accel"):
            return adis16475_channel_with_offset(ctrl, name)
        return adis16475_channel(ctrl, name)

    def __get_scaled_sensor(self, channel_name: str) -> float:
        raw = self._get_iio_attr(channel_name, "raw", False)
        scale = self._get_iio_attr(channel_name, "scale", False)

        return raw * scale

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

    def get_temp(self):
        """Value returned in millidegrees Celsius."""
        return self.__get_scaled_sensor("temp0")

    temp_conv = property(get_temp, None)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate in samples per second"""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def filter_low_pass_3db_frequency(self):
        """filter_low_pass_3db_frequency: Bandwidth for the accelerometer and
        gyroscope channels"""
        return self._get_iio_dev_attr("filter_low_pass_3db_frequency")

    @filter_low_pass_3db_frequency.setter
    def filter_low_pass_3db_frequency(self, value):
        self._set_iio_dev_attr_str("filter_low_pass_3db_frequency", value)

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

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
