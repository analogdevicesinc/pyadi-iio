# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp_no_buff


class ad7291_channel(attribute):
    """AD7291 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD7291 channel raw value"""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """AD7291 channel scale(gain)"""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    def __call__(self):
        """Utility function, returns millivolts"""
        return self.raw * self.scale


class ad7291_temp_channel(ad7291_channel):  # attribute):
    """AD7291 temperature channel"""

    @property
    def mean_raw(self):
        """AD7291 channel mean_raw value"""
        return self._get_iio_attr(self.name, "mean_raw", False)

    def __call__(self):
        """Utility function, returns deg. C"""
        return self.mean_raw * self.scale / 1000


class ad7291(rx_chan_comp_no_buff):
    """ AD7291 ADC """

    compatible_parts = ["ad7291"]
    _device_name = ""
    _complex_data = False

    def _channel_def(self, ctrl, name):
        if "temp" in name:
            return ad7291_temp_channel(ctrl, name)
        else:
            return ad7291_channel(ctrl, name)

    def __repr__(self):
        retstr = f"""
ad7291(uri="{self.uri}") object "{self._device_name}"
8-channel, I2C, 12-bit SAR ADC with temperature sensor

Channel layout:

voltageX.raw:              Raw 12-bit ADC code. read only for ADC channels
voltageX.scale:            ADC scale, millivolts per lsb
voltageX():                    Returns ADC reading in millivolts (read only)

temp0.raw:                      Temperature raw value
temp0.scale:                    Temperature scale value
temp0():                        Returns temperature in degrees Celsius

"""
        return retstr
