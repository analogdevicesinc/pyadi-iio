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

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ltc2314_14(rx, context_manager):
    """LTC2314-14 14-Bit, 4.5Msps Serial Sampling ADC

    parameters:
        uri: type=string
            URI of IIO context with LTC2314-14
    """

    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the main and trigger devices
        self._ctrl = self._ctx.find_device("ltc2314-14")
        self._trig = self._ctx.find_device("ltc2314_trigger")

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("LTC2314-14 device not found")

        # Raise an exception if the trigger isn't found
        if not self._trig:
            raise Exception("LTC2314-14 trigger not found")

        # Add the trigger to the main device
        self._ctrl.trigger = self._trig

        # Initialize the rx device
        rx.__init__(self)

        # Set the buffer length
        self.rx_buffer_size = 2

        # Set the sampling frequency for the trigger
        self.sampling_frequency = 10000

    @property
    def lsb_mv(self):
        """ Get/Set the LSB in millivolts """
        return self._get_iio_dev_attr("in_voltage_scale", self._ctrl)

    @lsb_mv.setter
    def lsb_mv(self, value):
        """ Get/Set the LSB in millivolts """
        self._set_iio_dev_attr_str("in_voltage_scale", value, self._ctrl)

    @property
    def sampling_frequency(self):
        """ Get/Set the sampling frequency for the trigger """
        return self._get_iio_dev_attr("sampling_frequency", self._trig)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """ Get/Set the sampling frequency for the trigger """
        self._set_iio_dev_attr_str("sampling_frequency", value, self._trig)


if __name__ == "__main__":
    adc = ltc2314_14("ip:192.168.1.18")
    print(adc.rx())
