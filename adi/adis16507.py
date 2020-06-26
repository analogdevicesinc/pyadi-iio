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


class adis16507(rx, context_manager):
    """ ADIS16507 Precision, Miniature MEMS IMU """

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

    def __init__(
        self, uri="", imu_dev_name="adis16507-3", trigger_name="adis16507-3-dev0"
    ):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(imu_dev_name)
        self._rxadc = self._ctx.find_device(imu_dev_name)
        # Set default trigger
        self._trigger = self._ctx.find_device(trigger_name)
        self._rxadc._set_trigger(self._trigger)
        rx.__init__(self)
        self.rx_buffer_size = 16  # Make default buffer smaller

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
    def current_timestamp_clock(self):
        """current_timestamp_clock: Source clock for timestamps"""
        return self._get_iio_dev_attr("current_timestamp_clock")

    @current_timestamp_clock.setter
    def current_timestamp_clock(self, value):
        self._set_iio_dev_attr_str("current_timestamp_clock", value)
