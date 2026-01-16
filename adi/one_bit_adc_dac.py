# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


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
            Dynamic instance properties will be created for each channel.
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

        # Store GPIO channel info for dynamic property handling
        # This fixes the bug where class-level properties were shared between instances
        self._gpio_channels = {}
        for chan in self._ctrl.channels:
            gpio_name = f"gpio_{chan.attrs['label'].value.lower()}"
            self._gpio_channels[gpio_name] = {
                "channel_id": chan.id,
                "output": chan.output,
            }

    def __getattribute__(self, name):
        """Custom attribute access to handle GPIO properties dynamically per instance"""
        # First try normal attribute access
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass

        # Check if it's a GPIO attribute
        if name.startswith("gpio_"):
            try:
                gpio_channels = object.__getattribute__(self, "_gpio_channels")
                if name in gpio_channels:
                    chan_info = gpio_channels[name]
                    ctrl = object.__getattribute__(self, "_ctrl")
                    return self._get_iio_attr(
                        chan_info["channel_id"], "raw", chan_info["output"], ctrl
                    )
            except AttributeError:
                # _gpio_channels doesn't exist yet (during initialization)
                pass

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name, value):
        """Custom attribute setting to handle GPIO properties dynamically per instance"""
        # Handle GPIO attributes if we have the channel info available
        if name.startswith("gpio_") and hasattr(self, "_gpio_channels"):
            gpio_channels = object.__getattribute__(self, "_gpio_channels")
            if name in gpio_channels:
                chan_info = gpio_channels[name]
                ctrl = object.__getattribute__(self, "_ctrl")
                self._set_iio_attr_int(
                    chan_info["channel_id"],
                    "raw",
                    chan_info["output"],
                    int(value),
                    ctrl,
                )
                return

        # Default behavior for all other attributes
        object.__setattr__(self, name, value)