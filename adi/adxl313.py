# Copyright (C) 2022 Analog Devices, Inc.
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
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adxl313(rx, context_manager, attribute):

    """ADXL313 3-axis accelerometer"""

    _device_name = ""
    _rx_data_type = np.int32
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri=""):
        """adxl313 class constructor."""
        context_manager.__init__(self, uri)

        compatible_parts = [
            "ADXL312",
            "ADXL313",
            "ADXL314",
        ]

        self._ctrl = None

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                print("Found device {}".format(device.name))
                self._ctrl = device
                self._rxadc = device
                self._device_name = device.name
                break

        if self._ctrl is None:
            raise Exception("No compatible device found")

        self.accel_x = self._channel(self._ctrl, "accel_x")
        self.accel_y = self._channel(self._ctrl, "accel_y")
        self.accel_z = self._channel(self._ctrl, "accel_z")
        self._rx_channel_names = ["accel_x", "accel_y", "accel_z"]
        rx.__init__(self)

    class _channel(attribute):

        """ADXL313 acceleration channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def calibbias(self):
            """ADXL313 channel offset."""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            self._set_iio_attr(self.name, "calibbias", False, value)

        @property
        def raw(self):
            """ADXL313 channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def sampling_frequency(self):
            """ADXL313 per-channel sampling frequency."""
            return float(self._get_iio_attr_str(self.name, "sampling_frequency", False))

        @sampling_frequency.setter
        def sampling_frequency(self, value):
            self._set_iio_attr_float(self.name, "sampling_frequency", False, value)

        @property
        def sampling_frequency_available(self):
            """Provides all available sampling frequency settings for the ADXL313 channels."""
            return self._get_iio_attr(self.name, "sampling_frequency_available", False)

        @property
        def range(self):
            """ADXL313 per-channel range."""
            return float(self._get_iio_attr_str(self.name, "range", False))

        @range.setter
        def range(self, value):
            self._set_iio_attr_float(self.name, "range", False, value)

        @property
        def range_available(self):
            """Provides all available range settings for the ADXL313 channels."""
            return self._get_iio_attr(self.name, "range_available", False)

        @property
        def scale(self):
            """ADXL313 channel scale(gain)."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr_float(self.name, "scale", False, value)

        @property
        def scale_available(self):
            """Provides all available scale settings for the ADXL313 channels."""
            return self._get_iio_attr(self.name, "scale_available", False)
