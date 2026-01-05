# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ltc2688(context_manager, attribute):
    """ LTC2688 DAC """

    _complex_data = False
    _device_name = "LTC2688"
    vref = 4.096
    channel_names = []

    def __init__(self, uri="ip:analog.local", device_index=0):
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device("ltc2688")

        for ch in self._ctrl.channels:
            name = ch.id
            self.channel_names.append(name)
            if "toggle_en" in ch.attrs:
                if "symbol" in ch.attrs:
                    setattr(self, name, self._channel_sw_toggle(self._ctrl, name))
                else:
                    setattr(self, name, self._channel_toggle(self._ctrl, name))
            elif "dither_en" in ch.attrs:
                setattr(self, name, self._channel_dither(self._ctrl, name))
            else:
                setattr(self, name, self._channel_standard(self._ctrl, name))

    class _channel_base(attribute):
        """ LTC2688 base channel class """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            """ LTC2688 channel gain """
            return self._get_iio_attr(self.name, "scale", True, self._ctrl)

        @property
        def offset(self):
            """ LTC2688 channel offset """
            return self._get_iio_attr(self.name, "offset", True, self._ctrl)

        @property
        def calibbias(self):
            """ LTC2688 channel calibbias property """
            return self._get_iio_attr(self.name, "calibbias", True, self._ctrl)

        @property
        def calibscale(self):
            """ LTC2688 channel calibbias scale """
            return self._get_iio_attr(self.name, "calibscale", True, self._ctrl)

        @property
        def powerdown(self):
            """ LTC2688 channel powerdown """
            return self._get_iio_attr_str(self.name, "powerdown", True)

        @powerdown.setter
        def powerdown(self, val):
            """ LTC2688 channel powerdown """
            self._set_iio_attr_str(self.name, "powerdown", True, val)

    class _channel_standard(_channel_base):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def raw(self):
            """ LTC2688 channel raw value property """
            return self._get_iio_attr(self.name, "raw", True, self._ctrl)

        @raw.setter
        def raw(self, val):
            """ LTC2688 channel raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw", True, str(int(val)))

        @property
        def volt(self):
            """ LTC2688 channel volt property """
            return ((self.raw + self.offset) * self.scale) * (ltc2688.vref / 4.096)

        @volt.setter
        def volt(self, val):
            """ LTC2688 channel volt setter """
            self.raw = int(((val / self.scale) - self.offset) * (ltc2688.vref / 4.096))

    class _channel_dither(_channel_standard):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def dither_en(self):
            """ LTC2688 channel dither enable flag """
            return self._get_iio_attr(self.name, "dither_en", True, self._ctrl)

        @dither_en.setter
        def dither_en(self, val):
            """ LTC2688 channel dither enable flag setter """
            self._set_iio_attr(self.name, "dither_en", True, val)

        @property
        def dither_frequency(self):
            """ LTC2688 channel dither frequency """
            return self._get_iio_attr(self.name, "dither_frequency", True, self._ctrl)

        @dither_frequency.setter
        def dither_frequency(self, val):
            """ LTC2688 channel dither frequency setter """
            dither_frequency_span = self._get_iio_attr(
                self.name, "dither_frequency_available", True, self._ctrl
            )
            for freq in dither_frequency_span:
                if val == freq:
                    self._set_iio_attr(self.name, "dither_frequency", True, val)
                    break

        @property
        def dither_phase(self):
            """ LTC2688 channel dither phase """
            return self._get_iio_attr(self.name, "dither_phase", True, self._ctrl)

        @dither_phase.setter
        def dither_phase(self, val):
            """ LTC2688 channel dither phase setter """
            dither_phase_span = self._get_iio_attr(
                self.name, "dither_phase_available", True, self._ctrl
            )
            for phase in dither_phase_span:
                if val == phase:
                    self._set_iio_attr(self.name, "dither_phase", True, val)
                    break

        @property
        def dither_raw(self):
            """ LTC2688 channel dither raw value property """
            return self._get_iio_attr(self.name, "dither_raw", True, self._ctrl)

        @dither_raw.setter
        def dither_raw(self, val):
            """ LTC2688 channel dither raw value property setter """
            dither_raw_span = self._get_iio_attr(
                self.name, "dither_raw_available", True, self._ctrl
            )
            if (
                val >= dither_raw_span[0]
                and val <= dither_raw_span[2]
                and val % dither_raw_span[1] == 0
            ):
                self._set_iio_attr(self.name, "dither_raw", True, str(int(val)))

        @property
        def dither_offset(self):
            """ LTC2688 channel dither offset """
            return self._get_iio_attr(self.name, "dither_offset", True, self._ctrl)

        @dither_offset.setter
        def dither_offset(self, val):
            """ LTC2688 channel dither offset setter """
            self._set_iio_attr(self.name, "dither_offset", True, str(int(val)))

    class _channel_toggle(_channel_base):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def toggle_en(self):
            """ LTC2688 channel toggle enable flag """
            return self._get_iio_attr(self.name, "toggle_en", True, self._ctrl)

        @toggle_en.setter
        def toggle_en(self, val):
            """ LTC2688 channel toggle enable flag setter """
            self._set_iio_attr(self.name, "toggle_en", True, val)

        @property
        def raw0(self):
            """ LTC2688 channel toggle state 0 raw value """
            return self._get_iio_attr(self.name, "raw0", True, self._ctrl)

        @raw0.setter
        def raw0(self, val):
            """ LTC2688 channel toggle state 0 raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw0", True, str(int(val)))

        @property
        def raw1(self):
            """ LTC2688 channel toggle state 1 raw value """
            return self._get_iio_attr(self.name, "raw1", True, self._ctrl)

        @raw1.setter
        def raw1(self, val):
            """ LTC2688 channel toggle state 1 raw value setter """
            raw_span = self._get_iio_attr(self.name, "raw_available", True, self._ctrl)
            if val >= raw_span[0] and val <= raw_span[2] and val % raw_span[1] == 0:
                self._set_iio_attr(self.name, "raw1", True, str(int(val)))

        @property
        def volt0(self):
            """ LTC2688 channel toggle state 0 voltage value """
            return ((self.raw0 + self.offset) * self.scale) * (ltc2688.vref / 4.096)

        @volt0.setter
        def volt0(self, val):
            """ LTC2688 channel toggle state 0 voltage value setter """
            self.raw0 = int(((val / self.scale) - self.offset) * (ltc2688.vref / 4.096))

        @property
        def volt1(self):
            """ LTC2688 channel toggle state 1 voltage value """
            return ((self.raw1 + self.offset) * self.scale) * (ltc2688.vref / 4.096)

        @volt1.setter
        def volt1(self, val):
            """ LTC2688 channel toggle state 1 voltage value setter """
            self.raw1 = int(((val / self.scale) - self.offset) * (ltc2688.vref / 4.096))

    class _channel_sw_toggle(_channel_toggle):
        def __init__(self, ctrl, channel_name):
            super().__init__(ctrl, channel_name)

        @property
        def toggle_state(self):
            """ LTC2688 SW toggle enable flag """
            return self._get_iio_attr(self.name, "symbol", True, self._ctrl)

        @toggle_state.setter
        def toggle_state(self, val):
            """ LTC2688 SW toggle enable flag setter """
            self._set_iio_attr(self.name, "symbol", True, str(int(val)))
