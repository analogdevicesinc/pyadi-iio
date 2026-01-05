# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ltc2664(context_manager, attribute):
    """ LTC2664 DAC """

    _complex_data = False
    _device_name = "LTC2664"
    channel_names = []

    def __init__(self, uri="ip:analog.local", device_index=0):
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ltc2664")

        for ch in self._ctrl.channels:
            name = ch.id
            self.channel_names.append(name)
            if "toggle_en" in ch.attrs:
                setattr(self, name, self._channel_toggle(self._ctrl, name))
            else:
                setattr(self, name, self._channel_standard(self._ctrl, name))

    class _channel_base(attribute):
        """ LTC2664 base channel class """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            """ LTC2664 channel gain """
            return self._get_iio_attr(self.name, "scale", True, self._ctrl)

        @property
        def offset(self):
            """ LTC2664 channel offset """
            return self._get_iio_attr(self.name, "offset", True, self._ctrl)

        @property
        def volt_available(self):
            """ LTC2664 voltage min/max [min, max] in mV """
            return [
                round((0 + self.offset) * self.scale, 2),
                round((65535 + self.offset) * self.scale, 2),
            ]

        @property
        def raw_available(self):
            """ LTC2664 raw value range [min, increment, max] """
            return list(
                map(
                    int,
                    (self._get_iio_attr(self.name, "raw_available", True, self._ctrl)),
                )
            )

        @property
        def powerdown(self):
            """ LTC2664 channel powerdown """
            return self._get_iio_attr(self.name, "powerdown", True, self._ctrl)

        @powerdown.setter
        def powerdown(self, val):
            """ LTC2664 channel powerdown """
            self._set_iio_attr(self.name, "powerdown", True, val, self._ctrl)

    class _channel_standard(_channel_base):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def raw(self):
            """ LTC2664 channel raw value property """
            return self._get_iio_attr(self.name, "raw", True, self._ctrl)

        @raw.setter
        def raw(self, val):
            """ LTC2664 channel raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw", True, str(int(val)))

        @property
        def volt(self):
            """ LTC2664 channel volt property (in mV)"""
            return (self.raw + self.offset) * self.scale

        @volt.setter
        def volt(self, val):
            """ LTC2664 channel volt setter (in mV)"""
            self.raw = int((val / self.scale) - self.offset)

    class _channel_toggle(_channel_base):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def toggle_en(self):
            """ LTC2664 channel toggle enable flag """
            return self._get_iio_attr(self.name, "toggle_en", True, self._ctrl)

        @toggle_en.setter
        def toggle_en(self, val):
            """ LTC2664 channel toggle enable flag setter """
            self._set_iio_attr(self.name, "toggle_en", True, val)

        @property
        def toggle_state(self):
            """ LTC2664 SW toggle enable flag """
            return self._get_iio_attr(self.name, "symbol", True, self._ctrl)

        @toggle_state.setter
        def toggle_state(self, val):
            """ LTC2664 SW toggle enable flag setter """
            self._set_iio_attr(self.name, "symbol", True, str(int(val)))

        @property
        def raw0(self):
            """ LTC2664 channel toggle state 0 raw value """
            return self._get_iio_attr(self.name, "raw0", True, self._ctrl)

        @raw0.setter
        def raw0(self, val):
            """ LTC2664 channel toggle state 0 raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw0", True, str(int(val)))

        @property
        def raw1(self):
            """ LTC2664 channel toggle state 1 raw value """
            return self._get_iio_attr(self.name, "raw1", True, self._ctrl)

        @raw1.setter
        def raw1(self, val):
            """ LTC2664 channel toggle state 1 raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw1", True, str(int(val)))

        @property
        def volt0(self):
            """ LTC2664 channel toggle state 0 voltage value (in mV)"""
            return (self.raw0 + self.offset) * self.scale

        @volt0.setter
        def volt0(self, val):
            """ LTC2664 channel toggle state 0 voltage value setter (in mV)"""
            self.raw0 = int(((val / self.scale) - self.offset))

        @property
        def volt1(self):
            """ LTC2664 channel toggle state 1 voltage value (in mV)"""
            return (self.raw1 + self.offset) * self.scale

        @volt1.setter
        def volt1(self, val):
            """ LTC2664 channel toggle state 1 voltage value setter (in mV)"""
            self.raw1 = int(((val / self.scale) - self.offset))
