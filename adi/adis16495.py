# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numpy as np
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adis16495(rx, context_manager):
    """ADIS16495 Precision, Miniature MEMS IMU."""

    _complex_data = False
    _rx_channel_names = [
        "anglvel_x",
        "anglvel_y",
        "anglvel_z",
        "accel_x",
        "accel_y",
        "accel_z",
    ]
    _device_name = ""
    _rx_data_type = ">i4"
    _rx_data_si_type = np.float

    def __init__(self, uri="", name="adis16495-3"):
        """Initialize an adis16495 object.

        parameters:
            uri: type=string
                URI of IIO context with adis16495.
            name: type=string
                Name of the device. Set to adis16495-3
                by default.
        """
        trigger_name = name + "-dev0"
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(name)
        self._rxadc = self._ctx.find_device(name)
        # Set default trigger
        self._trigger = self._ctx.find_device(trigger_name)
        self._rxadc._set_trigger(self._trigger)
        rx.__init__(self)
        self.rx_buffer_size = 16  # Make default buffer smaller

    # device attributes
    @property
    def sample_rate(self):
        """Sample_rate: Sample rate in samples per second."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def current_timestamp_clock(self):
        """Current_timestamp_clock: Source clock for timestamps."""
        return self._get_iio_dev_attr("current_timestamp_clock")

    @current_timestamp_clock.setter
    def current_timestamp_clock(self, value):
        self._set_iio_dev_attr_str("current_timestamp_clock", value)

    # channel attributes
    def get_temp(self):
        """Value returned in millidegrees celsius."""
        raw = self._get_iio_attr("temp0", "raw", False)
        off = self._get_iio_attr("temp0", "offset", False)
        scale = self._get_iio_attr("temp0", "scale", False)

        return (raw + off) * scale

    temperature = property(get_temp, None)

    def __get_scaled_sensor(self, channel_name: str) -> float:
        raw = self._get_iio_attr(channel_name, "raw", False)
        scale = self._get_iio_attr(channel_name, "scale", False)

        return raw * scale

    # get anglvel_x related attributes
    def get_anglvel_x(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_x")

    anglvel_x = property(get_anglvel_x, None)

    @property
    def anglvel_x_filter_low_pass_3db_frequency(self):
        return self._get_iio_attr("anglvel_x", "filter_low_pass_3db_frequency", False)

    @anglvel_x_filter_low_pass_3db_frequency.setter
    def anglvel_x_filter_low_pass_3db_frequency(self, value):
        """Value returned in HZ."""
        self._set_iio_attr("anglvel_x", "filter_low_pass_3db_frequency", False, value)

    @property
    def anglvel_x_calibbias(self):
        """User bias adjustment for the x-axis."""
        return self._get_iio_attr("anglvel_x", "calibbias", False)

    @anglvel_x_calibbias.setter
    def anglvel_x_calibbias(self, value):
        self._set_iio_attr("anglvel_x", "calibbias", False, value)

    @property
    def anglvel_x_calibscale(self):
        """User scale adjustment for the x-axis."""
        return self._get_iio_attr("anglvel_x", "calibscale", False)

    @anglvel_x_calibscale.setter
    def anglvel_x_calibscale(self, value):
        self._set_iio_attr("anglvel_x", "calibscale", False, value)

    # get anglvel_y related attributes
    def get_anglvel_y(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_y")

    anglvel_y = property(get_anglvel_y, None)

    @property
    def anglvel_y_filter_low_pass_3db_frequency(self):
        """Value returned in HZ."""
        return self._get_iio_attr("anglvel_y", "filter_low_pass_3db_frequency", False)

    @anglvel_y_filter_low_pass_3db_frequency.setter
    def anglvel_y_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("anglvel_y", "filter_low_pass_3db_frequency", False, value)

    @property
    def anglvel_y_calibbias(self):
        """User bias adjustment for the y-axis."""
        return self._get_iio_attr("anglvel_y", "calibbias", False)

    @anglvel_y_calibbias.setter
    def anglvel_y_calibbias(self, value):
        self._set_iio_attr("anglvel_y", "calibbias", False, value)

    @property
    def anglvel_y_calibscale(self):
        """User scale adjustment for the y-axis."""
        return self._get_iio_attr("anglvel_y", "calibscale", False)

    @anglvel_y_calibscale.setter
    def anglvel_y_calibscale(self, value):
        self._set_iio_attr("anglvel_y", "calibscale", False, value)

    # get anglvel_z related attributes
    def get_anglvel_z(self):
        """Value returned in radians per second."""
        return self.__get_scaled_sensor("anglvel_z")

    anglvel_z = property(get_anglvel_z, None)

    @property
    def anglvel_z_filter_low_pass_3db_frequency(self):
        """Value returned in HZ."""
        return self._get_iio_attr("anglvel_z", "filter_low_pass_3db_frequency", False)

    @anglvel_z_filter_low_pass_3db_frequency.setter
    def anglvel_z_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("anglvel_z", "filter_low_pass_3db_frequency", False, value)

    @property
    def anglvel_z_calibbias(self):
        """User bias adjustment for the z-axis."""
        return self._get_iio_attr("anglvel_z", "calibbias", False)

    @anglvel_z_calibbias.setter
    def anglvel_z_calibbias(self, value):
        self._set_iio_attr("anglvel_z", "calibbias", False, value)

    @property
    def anglvel_z_calibscale(self):
        """User scale adjustment for the z-axis."""
        return self._get_iio_attr("anglvel_z", "calibscale", False)

    @anglvel_z_calibscale.setter
    def anglvel_z_calibscale(self, value):
        self._set_iio_attr("anglvel_z", "calibscale", False, value)

    # get accel_x related attributes
    def get_accel_x(self):
        """Value returned in m/s^2."""
        return self.__get_scaled_sensor("accel_x")

    accel_x = property(get_accel_x, None)

    @property
    def accel_x_filter_low_pass_3db_frequency(self):
        """Value returned in HZ."""
        return self._get_iio_attr("accel_x", "filter_low_pass_3db_frequency", False)

    @accel_x_filter_low_pass_3db_frequency.setter
    def accel_x_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_x", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_x_calibbias(self):
        """User bias adjustment for the x-axis."""
        return self._get_iio_attr("accel_x", "calibbias", False)

    @accel_x_calibbias.setter
    def accel_x_calibbias(self, value):
        self._set_iio_attr("accel_x", "calibbias", False, value)

    @property
    def accel_x_calibscale(self):
        """User scale adjustment for the x-axis."""
        return self._get_iio_attr("accel_x", "calibscale", False)

    @accel_x_calibscale.setter
    def accel_x_calibscale(self, value):
        self._set_iio_attr("accel_x", "calibscale", False, value)

    # get accel_y related attributes
    def get_accel_y(self):
        """Value returned in m/s^2."""
        return self.__get_scaled_sensor("accel_y")

    accel_y = property(get_accel_y, None)

    @property
    def accel_y_filter_low_pass_3db_frequency(self):
        """Value returned in HZ."""
        return self._get_iio_attr("accel_y", "filter_low_pass_3db_frequency", False)

    @accel_y_filter_low_pass_3db_frequency.setter
    def accel_y_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_y", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_y_calibbias(self):
        """User bias adjustment for the y-axis."""
        return self._get_iio_attr("accel_y", "calibbias", False)

    @accel_y_calibbias.setter
    def accel_y_calibbias(self, value):
        self._set_iio_attr("accel_y", "calibbias", False, value)

    @property
    def accel_y_calibscale(self):
        """User scale adjustment for the y-axis."""
        return self._get_iio_attr("accel_y", "calibscale", False)

    @accel_y_calibscale.setter
    def accel_y_calibscale(self, value):
        self._set_iio_attr("accel_y", "calibscale", False, value)

    # get accel_y related attributes
    def get_accel_z(self):
        """Value returned in m/s^2."""
        return self.__get_scaled_sensor("accel_z")

    accel_z = property(get_accel_z, None)

    @property
    def accel_z_filter_low_pass_3db_frequency(self):
        """Value returned in HZ."""
        return self._get_iio_attr("accel_z", "filter_low_pass_3db_frequency", False)

    @accel_z_filter_low_pass_3db_frequency.setter
    def accel_z_filter_low_pass_3db_frequency(self, value):
        self._set_iio_attr("accel_z", "filter_low_pass_3db_frequency", False, value)

    @property
    def accel_z_calibbias(self):
        """User bias adjustment for the z-axis."""
        return self._get_iio_attr("accel_z", "calibbias", False)

    @accel_z_calibbias.setter
    def accel_z_calibbias(self, value):
        self._set_iio_attr("accel_z", "calibbias", False, value)

    @property
    def accel_z_calibscale(self):
        return self._get_iio_attr("accel_z", "calibscale", False)

    @accel_z_calibscale.setter
    def accel_z_calibscale(self, value):
        """User scale adjustment for the z-axis."""
        self._set_iio_attr("accel_z", "calibscale", False, value)
