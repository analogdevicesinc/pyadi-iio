# Copyright (C) 2019-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad7124(rx, context_manager):
    """ AD7124 ADC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_index=0):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad7124-8", "ad7124-4"]

        self._ctrl = None
        index = 0

        # Selecting the device_index-th device from the 7124 family as working device.
        for device in self._ctx.devices:
            if device.name in compatible_parts:
                if index == device_index:
                    self._ctrl = device
                    self._rxadc = device
                    break
                else:
                    index += 1

        # dynamically get channels and sorting them after the index of the first voltage channel
        self._ctrl.channels.sort(key=lambda x: int(x.id[7 : x.id.find("-")]))

        for ch in self._ctrl.channels:
            name = ch._id
            self._rx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
        rx.__init__(self)

    def rx(self):
        sig = super().rx()

        if (
            self._rx_unbuffered_data
            or self._complex_data
            or self.rx_output_type == "raw"
        ):
            return sig
        else:
            mv_sig = []

            for signal in sig:
                mv_sig.append(signal / 1000)

            return mv_sig

    @property
    def sample_rate(self):
        """Sets sampling frequency of the AD7124"""
        return self._get_iio_attr(self.channel[0].name, "sampling_frequency", False)

    @sample_rate.setter
    def sample_rate(self, value):
        for ch in self.channel:
            self._set_iio_attr(ch.name, "sampling_frequency", False, value)

    @property
    def scale_available(self):
        """Provides all available scale(gain) settings for the AD7124 channels"""
        return self._get_iio_attr(self.channel[0].name, "scale_available", False)
