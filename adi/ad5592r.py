# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad5592r(rx, context_manager):
    """AD5592R and AD5593R SPI / I2C interface, 8-channel, 12-bit Confiburable ADC/DAC, digital GPIO

    Analog I/O pins are configured in the device tree and can be ADC, DAC, or both. Channel attributes are as follows, where X corresponds to device channel number:
        voltageX_adc.raw:              Raw 12-bit ADC code. read only for ADC channels\n
        voltageX_adc.scale:            ADC scale, millivolts per lsb\n
        voltageX_adc.scale_available:  Available scales, corresponding to Vref*1, Vref*2\n
        voltageX():                    Returns ADC reading in millivolts (read only)\n
        voltageX_dac.raw:              Raw 12-bit DAC code. read/write for DAC channels\n
        voltageX_dac.scale:            ADC scale, millivolts per lsb\n
        voltageX_dac.scale_available:  Available scales (corresponding to 1X/2X gain)\n
        voltageX(1234.5):              Sets/Returns ADC reading in millivolts\n
        temp.raw:                      Temperature raw value\n
        temp.scale:                    Temperature scale value\n
        temp.offset                    Temperature offset value\n
        temp():                        Returns temperature in degrees Celsius\n
    """

    _device_name = ""
    _complex_data = False
    channel = []

    def __repr__(self):
        retstr = f"""
ad5592r(uri="{self.uri}, device_name={self._device_name})"

{self.__doc__}
"""

        return retstr

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad5592r",
            "ad5593r",
        ]

        self.ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Selecting the device matching device_name AD559XR family as working device.
        for device in self._ctx.devices:
            if device.name in device_name:
                self._ctrl = device
                self._rxadc = device
                buffers_avail = any([c.scan_element for c in self._rxadc.channels])
                if not buffers_avail:
                    delattr(self, "rx")
                break

        self.channel = []
        self._rx_channel_names = []

        # Dynamically get channels after the index
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            if name == "temp":
                setattr(self, name, self.channel_temp(self._ctrl, name, output))
            else:
                if output is True:
                    setattr(
                        self, name + "_dac", self.channel_dac(self._ctrl, name, output)
                    )
                else:
                    self._rx_channel_names.append(name)
                    self.channel.append(self.channel_adc(self._ctrl, name, output))
                    setattr(
                        self, name + "_adc", self.channel_adc(self._ctrl, name, output)
                    )
        rx.__init__(self)

    class channel_adc(attribute):
        """AD5592R Input Voltage Channels"""

        # AD559XR ADC channel
        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        # AD559XR channel raw value, property only for ADC channels
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self._output)

        @property
        # AD559XR channel scale (gain)
        def scale(self):
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @scale.setter
        def scale(self, value):
            scale_available = self._get_iio_attr(
                self.name, "scale_available", self._output
            )
            for scale_available_0 in scale_available:
                if scale_available_0 == value:
                    self._set_iio_attr(
                        self.name,
                        "scale",
                        self._output,
                        value,  # str(Decimal(value).real) # Why do some device classes use Decimal??
                    )

        @property
        def scale_available(self):
            """Available scales"""
            return self._get_iio_attr(self.name, "scale_available", self._output)

        def __call__(self, mV=None):
            """Convenience function, set / get voltages in SI units (millivolts)"""
            if mV is not None:
                self.raw = int(float(mV) / float(self.scale))
            return self.raw * self.scale

    class channel_dac(channel_adc):
        """AD5592R Output Voltage Channels
        (Add setter to raw property)"""

        # AD559XR DAC channel
        def __init__(self, ctrl, channel_name, output):
            super().__init__(ctrl, channel_name, output)

        @property
        # AD559XR channel raw value
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self._output)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", self._output, value)

    class channel_temp(attribute):
        """AD5592R Temperature Channel"""

        # AD559XR voltage channel
        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        # AD559XR channel raw value
        def raw(self):
            return self._get_iio_attr(self.name, "raw", self._output)

        @property
        # AD559XR channel scale (gain)
        def scale(self):
            return float(self._get_iio_attr_str(self.name, "scale", self._output))

        @property
        # AD559XR channel temp offset value
        def offset(self):
            return self._get_iio_attr(self.name, "offset", self._output)

        def __call__(self, mV=None):
            """Convenience function, get temperature in SI units (Degrees C)"""
            return ((self.raw + self.offset) * self.scale) / 1000
