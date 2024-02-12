# Copyright (C) 2020-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7944(rx, context_manager):
    """AD7944, 14-bit, successive approximation analog-to-digital
    converter (SAR ADC) with sample rates up to 2.5 MSPS"""

    _compatible_parts = ["ad7944"]
    _device_name = ""
    _rx_data_type = np.uint16

    _rx_channel_names = []

    def __init__(self, uri="ip:analog.local", device_name="ad7944"):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        if not device_name:
            device_name = self._compatible_parts[0]
        else:
            if device_name not in self._compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        # TODO: if/when pyadi-iio and libiio get refactored, this could
        # be done more gracefully. The device object should have a
        # trigger property that is directly accessible for the sampling
        # frequency, but this is broken in libiio 0.25.
        trigger_name = "trigger0"
        self._rxadc = self._ctrl = self._ctx.find_device(device_name)
        self._trigger = self._ctx.find_device(trigger_name)

        if not self._ctrl:
            raise Exception(f"Error in selecting matching device {device_name}")

        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._trigger.frequency

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        self._trigger.frequency = rate


class ad7985(ad7944):
    """AD7985, 16-bit, successive approximation analog-to-digital
    converter (SAR ADC) with sample rates up to 2.5 MSPS"""

    _compatible_parts = ["ad7985"]
    _rx_data_type = np.uint16

    def __init__(self, uri="ip:analog.local", device_name="ad7985"):
        super().__init__(uri, device_name)


class ad7986(ad7944):
    """AD7986, 18-bit, successive approximation analog-to-digital
    converter (SAR ADC) with sample rates up to 2 MSPS"""

    _compatible_parts = ["ad7986"]
    _rx_data_type = np.int32

    def __init__(self, uri="ip:analog.local", device_name="ad7986"):
        super().__init__(uri, device_name)
