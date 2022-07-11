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

from abc import abstractmethod
from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adc_separate_channels(rx, context_manager):
    """ADCs with independent channels common core"""

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Common constructor for ADCs with separate channel configurations."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None
        self._rxadc = None

        if not device_name:
            device_name = self.compatible_parts[0]
        elif device_name not in self.compatible_parts:
            raise Exception(f"Not a compatible device: {device_name}")

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        if not self._ctrl or not self._rxadc:
            raise Exception(f"Error in selecting matching device {device_name}")

        for ch in self._ctrl.channels:
            self._rx_channel_names.append(ch._id)
            self.channel.append(self._channel(self._ctrl, ch._id))

        rx.__init__(self)

    @property
    @abstractmethod
    def compatible_parts(self) -> None:
        """List of compatible driver names."""
        raise NotImplementedError  # pragma: no cover

    class _channel(attribute):

        """Channel configuration"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """Channel raw value."""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def offset(self):
            """Channel offset."""
            return float(self._get_iio_attr_str(self.name, "offset", False))

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", False, str(Decimal(value).real))

        @property
        def scale(self):
            """Channel scale."""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))

    def to_volts(self, index, val):
        """Converts raw value to SI."""
        _scale = self.channel[index].scale

        ret = None

        if isinstance(val, np.int16):
            ret = val * _scale

        if isinstance(val, np.ndarray):
            ret = [x * _scale for x in val]

        return ret


class ad4110(adc_separate_channels):

    """AD4110 ADC"""

    _rx_data_type = np.int32
    compatible_parts = ["ad4110"]


class ad4130(adc_separate_channels):

    """AD4130 ADC"""

    compatible_parts = ["ad4130-8"]


class ad717x(adc_separate_channels):

    """AD717x ADC"""

    compatible_parts = [
        "ad4111",
        "ad4112",
        "ad4114",
        "ad4115",
        "ad7172-2",
        "ad7172-4",
        "ad7173-8",
        "ad7175-2",
        "ad7175-8",
        "ad7176-2",
        "ad7177-2",
    ]
