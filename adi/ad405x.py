# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
# Copyright (C) 2023 Analog Devices, Inc.
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

from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad405x(rx, context_manager):
    """ AD405x ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad4052", "ad4050"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        rx.__init__(self)

    @property
    def operating_mode_avail(self):
        """Get available operating modes."""
        return self._get_iio_dev_attr_str("operating_mode_available")

    @property
    def operating_mode(self):
        """Get operating mode."""
        return self._get_iio_dev_attr_str("operating_mode")

    @operating_mode.setter
    def operating_mode(self, value):
        """Set operating mode."""
        if value in self.operating_mode_avail:
            self._set_iio_dev_attr_str("operating_mode", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.operating_mode_avail)
            )

    @property
    def burst_sample_rate(self):
        """Get burst sample rate. Only available in Burst Averaging Mode."""
        if "burst_sample_rate" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("burst_sample_rate")
        else:
            raise ValueError(
                "Error: Burst sample rate not supported in " + self.operating_mode
            )

    @burst_sample_rate.setter
    def burst_sample_rate(self, value):
        """Set burst sample rate."""
        if "burst_sample_rate" in self._ctrl._attrs.keys():
            self._set_iio_dev_attr("burst_sample_rate", value)
        else:
            raise Exception(
                "Error: Burst sample rate not supported in " + self.operating_mode
            )

    @property
    def avg_filter_length_avail(self):
        """Get available average filter length. Only available in Burst Averaging Mode."""
        if "avg_filter_length_available" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("avg_filter_length_available")
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @property
    def avg_filter_length(self):
        """Get average filter length. Only available in Burst Averaging Mode."""
        if "avg_filter_length" in self._ctrl._attrs.keys():
            return self._get_iio_dev_attr("avg_filter_length")
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @avg_filter_length.setter
    def avg_filter_length(self, value):
        """Set average filter length."""
        if "avg_filter_length_available" in self._ctrl._attrs.keys():
            if value in self.avg_filter_length_avail:
                self._set_iio_dev_attr("avg_filter_length", value)
            else:
                raise ValueError(
                    "Error: Average filter length not supported \nUse one of: "
                    + str(self.avg_filter_length_avail)
                )
        else:
            raise Exception(
                "Error: Average filter length not supported in " + self.operating_mode
            )

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling_frequency."""
        self._set_iio_dev_attr("sampling_frequency", value)

    class _channel(attribute):
        """AD405x channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """AD405x channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def offset(self):
            """AD405x channel system calibration"""
            return self._get_iio_attr_str(self.name, "offset", False)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))

        @property
        def scale(self):
            """AD405x channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    def to_volts(self, index, val):
        """Converts raw value to SI"""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.uint16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret
