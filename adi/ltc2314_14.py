# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp_no_buff


class ltc2314_14_channel(attribute):
    """LTC2314-14 Channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def lsb_mv(self):
        """ Get the LSB in millivolts """
        return self._get_iio_attr("voltage0", "scale", False, self._ctrl)

    @property
    def voltage(self):
        """ Get the voltage reading from the ADC """
        code = self._get_iio_attr("voltage0", "raw", False, self._ctrl)
        return code * self.lsb_mv / 1000


class ltc2314_14(rx_chan_comp_no_buff):
    """LTC2314-14 14-Bit, 4.5Msps Serial Sampling ADC

    parameters:
        uri: type=string
            URI of IIO context with LTC2314-14
    """

    compatible_parts = ["ltc2314-14"]
    _device_name = ""
    _complex_data = False
    _channel_def = ltc2314_14_channel
