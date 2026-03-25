# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad7291(context_manager):
    """ AD7291 ADC """

    _device_name = ""

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

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7291"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the 7291 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    break
                else:
                    index += 1

        for ch in self._ctrl.channels:
            name = ch._id
            if "temp" in name:

                setattr(self, name, self._temp_channel(self._ctrl, name))

            else:
                name = ch._id
                setattr(self, name, self._channel(self._ctrl, name))

    class _channel(attribute):
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

    class _temp_channel(_channel):  # attribute):
        """AD7291 temperature channel"""

        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def mean_raw(self):
            """AD7291 channel mean_raw value"""
            return self._get_iio_attr(self.name, "mean_raw", False)

        def __call__(self):
            """Utility function, returns deg. C"""
            return self.mean_raw * self.scale / 1000
