# Copyright (C) 2021 Analog Devices, Inc.
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

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adpd410x(rx, context_manager):
    """ adpd410x Multimodal Sensor Front End """

    _complex_data = False
    channel = []  # type: ignore
    _rx_channel_names = [
        "channel0",
        "channel1",
        "channel2",
        "channel3",
        "channel4",
        "channel5",
        "channel6",
        "channel7",
    ]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("adpd410x")

        for name in self._rx_channel_names:
            self.channel.append(self._channel(self._rxadc, name))

    @property
    def sampling_frequency(self):
        """Get sampling frequency of the adpd410x"""
        return self._get_iio_dev_attr_str("sampling_frequency", self._rxadc)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Sets sampling frequency of the adpd410x"""
        self._set_iio_dev_attr_str("sampling_frequency", value, self._rxadc)

    @property
    def last_timeslot(self):
        """Get last timeslot of the adpd410x"""
        return self._get_iio_dev_attr_str("last_timeslot", self._rxadc)

    @last_timeslot.setter
    def last_timeslot(self, value):
        """Sets last timeslot of the adpd410x"""
        self._set_iio_dev_attr_str("last_timeslot", value, self._rxadc)

    @property
    def operation_mode(self):
        """Get operation mode of the adpd410x"""
        return self._get_iio_dev_attr_str("operation_mode", self._rxadc)

    @operation_mode.setter
    def operation_mode(self, value):
        """Sets operation mode of the adpd410x"""
        self._set_iio_dev_attr_str("operation_mode", value, self._rxadc)

    class _channel(attribute):
        """adpd410x channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ adpd410x channel raw value"""
            return self._get_iio_attr(self.name, "raw", False, self._ctrl)
