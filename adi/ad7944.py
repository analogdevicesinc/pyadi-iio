# Copyright (C) 2020-2025 Analog Devices, Inc.
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

    def __init__(self, uri="ip:analog.local", device_name="ad7944"):
        """Initialize."""
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        if not device_name:
            device_name = self._compatible_parts[0]
        else:
            if device_name not in self._compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        self._rxadc = self._ctrl = self._ctx.find_device(device_name)

        if not self._rxadc:
            raise Exception(f"Error in selecting matching device {device_name}")

        if not self._ctrl:
            raise Exception(f"Error in selecting matching device {device_name}")

        self._rx_channel_names = []
        for ch in self._rxadc.channels:
            name = ch._id
            self._rx_channel_names.append(name)

        # The data type depends on whether or not SPI offload support is
        # available. We can check this by testing for the
        # sampling_frequency_available attribute, as this only exists in that
        # case.
        try:
            self._get_iio_attr(
                self.rx_channel_names[0], "sampling_frequency_available", False
            )
            self._rx_data_type = np.uint32
        except KeyError:
            self._rx_data_type = np.uint16

        rx.__init__(self)

    @property
    def sampling_frequency(self):
        """Get sampling frequency."""
        return self._get_iio_attr(self.rx_channel_names[0], "sampling_frequency", False)

    @property
    def sampling_frequency_available(self):
        """Get available sampling frequency values. This property only exists if
        SPI offload is enabled for the driver."""
        if isinstance(self._rx_data_type, np.uint32):
            return self._get_iio_attr(
                self.rx_channel_names[0], "sampling_frequency_available", False
            )
        else:
            pass

    @sampling_frequency.setter
    def sampling_frequency(self, rate):
        """Set sampling frequency."""
        self._set_iio_attr(
            self.rx_channel_names[0], "sampling_frequency", value=rate, output=False
        )


class ad7985(ad7944):
    """AD7985, 16-bit, successive approximation analog-to-digital
    converter (SAR ADC) with sample rates up to 2.5 MSPS"""

    _compatible_parts = ["ad7985"]

    def __init__(self, uri="ip:analog.local", device_name="ad7985"):
        super().__init__(uri, device_name)


class ad7986(ad7944):
    """AD7986, 18-bit, successive approximation analog-to-digital
    converter (SAR ADC) with sample rates up to 2 MSPS"""

    _compatible_parts = ["ad7986"]

    def __init__(self, uri="ip:analog.local", device_name="ad7986"):
        super().__init__(uri, device_name)
        self._rx_data_type = np.int32
