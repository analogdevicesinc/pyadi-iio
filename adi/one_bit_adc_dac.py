# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class _dyn_property:
    """ Class descriptor for accessing individual attributes """

    def __init__(self, attr, dev, channel_name, output):
        self._dev = dev
        self._attr = attr
        self._channel_name = channel_name
        self._output = output

    def __get__(self, instance, owner):
        return instance._get_iio_attr(
            self._channel_name, self._attr, self._output, self._dev
        )

    def __set__(self, instance, value):
        instance._set_iio_attr_int(
            self._channel_name, self._attr, self._output, int(value), self._dev
        )


class one_bit_adc_dac(attribute, context_manager):
    """One bit ADC/DAC (GPIO). This driver will create a handle for the
        GPIO device as well as properties for each GPIO pin it accesses.
        Each GPIO pin name will be lowercase and of the format:
        "gpio_{pin name}"

    parameters:
        uri: type=string
            URI of IIO context with GPIO pins
        name: type=string
            String identifying the device by name from the device tree.
            Dynamic class properties will be created for each channel.
    """

    _device_name = ""

    def __init__(self, uri="", name="one-bit-adc-dac"):

        try:
            context_manager.__init__(self, uri, self._device_name)
        except Exception:
            raise Exception(f"No device found for {name}")

        self._ctrl = None

        for dev in self._ctx.devices:
            if "label" in dev.attrs and dev.attrs["label"].value == name:
                self._ctrl = dev
                break
            else:
                if dev.name == name:
                    self._ctrl = dev
                    break

        if not self._ctrl:
            raise Exception(f"No device found for {name}")

        for chan in self._ctrl.channels:
            setattr(
                type(self),
                f"gpio_{chan.attrs['label'].value.lower()}",
                _dyn_property(
                    "raw", dev=self._ctrl, channel_name=chan.id, output=chan.output
                ),
            )
