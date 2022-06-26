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


class ad7768(rx, context_manager):

    """ AD7768 8-channel, Simultaneous Sampling Sigma-Delta ADC """

    _device_name = " "
    _rx_data_type = np.int32

    def __init__(
        self, uri="ip:analog.local",
    ):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ad7768")
        self._rxadc = self._ctx.find_device("ad7768")
        self._device_name = "ad7768"
        if not self._rxadc:
            self._ctrl = self._ctx.find_device("cf_axi_adc")
            self._rxadc = self._ctx.find_device("cf_axi_adc")
            self._device_name = "cf_axi_adc"

        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)
        rx.__init__(self)

    @property
    def sampling_frequency_available(self):
        """Get available sampling frequencies."""
        return self._get_iio_dev_attr("sampling_frequency_available")

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        if rate in self.sampling_frequency_available:
            self._set_iio_dev_attr("sampling_frequency", rate)
        else:
            raise ValueError(
                "Error: Sampling frequency not supported \nUse one of: "
                + str(self.sampling_frequency_available)
            )

    @property
    def power_mode_avail(self):
        """Get available power modes."""
        return self._get_iio_dev_attr_str("power_mode_available")

    @property
    def power_mode(self):
        """Get power mode."""
        return self._get_iio_dev_attr_str("power_mode")

    @power_mode.setter
    def power_mode(self, mode):
        """Set power mode."""
        if mode in self.power_mode_avail:
            self._set_iio_dev_attr_str("power_mode", mode)
        else:
            raise ValueError(
                "Error: Power mode not supported \nUse one of: "
                + str(self.power_mode_avail)
            )

    @property
    def filter_type_avail(self):
        """Get available filter types."""
        return self._get_iio_dev_attr_str("filter_type_available")

    @property
    def filter_type(self):
        """Get filter type."""
        return self._get_iio_dev_attr_str("filter_type")

    @filter_type.setter
    def filter_type(self, ftype):
        """Set filter type."""
        if ftype in self.filter_type_avail:
            self._set_iio_dev_attr_str("filter_type", ftype)
        else:
            raise ValueError(
                "Error: Filter type not supported \nUse one of: "
                + str(self.filter_type_avail)
            )
