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

import time

from adi.cn0540 import cn0540


class cn0532(cn0540):
    """ CN0532: Custom board with ADXL1002 Low Noise, High Frequency +/-50g MEMS Accelerometer """

    def __init__(self, uri=""):

        cn0540.__init__(self, uri=uri)

    def calibrate(self):
        """ Tune LTC2606 to make AD7768-1 ADC codes zero mean """
        adc_chan = self._rxadc
        dac_chan = self._ltc2606
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        dac_scale = float(self._get_iio_attr("voltage0", "scale", True, dac_chan))

        for _ in range(20):
            raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
            adc_voltage = raw * adc_scale

            raw = self._get_iio_attr("voltage0", "raw", True, dac_chan)
            dac_voltage = (raw * dac_scale - adc_voltage) / dac_scale

            self._set_iio_attr_float(
                "voltage0", "raw", True, int(dac_voltage), dac_chan
            )
            time.sleep(0.01)
